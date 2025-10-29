"""
Device Optimizer - 智能设备检测和参数优化
自动检测GPU型号、显存大小，并提供优化参数
"""

import subprocess
import re
from typing import Dict, Optional, Tuple


class DeviceOptimizer:
    """设备优化器 - 自动检测GPU并优化参数"""
    
    # GPU型号到计算能力的映射
    GPU_COMPUTE_CAPABILITY = {
        'H100': ('90', 'Hopper', 70000),
        'H800': ('90', 'Hopper', 70000),
        'A100': ('80', 'Ampere', 40000),
        'A800': ('80', 'Ampere', 40000),
        'A40': ('86', 'Ampere', 40000),
        'A30': ('86', 'Ampere', 20000),
        'A10': ('86', 'Ampere', 20000),
        'A16': ('86', 'Ampere', 16000),
        'RTX 4090': ('89', 'Ada Lovelace', 24000),
        'RTX 4080': ('89', 'Ada Lovelace', 16000),
        'RTX 4070': ('89', 'Ada Lovelace', 12000),
        'RTX 4060': ('89', 'Ada Lovelace', 8000),
        'RTX 3090': ('86', 'Ampere', 24000),
        'RTX 3080': ('86', 'Ampere', 10000),
        'RTX 3070': ('86', 'Ampere', 8000),
        'RTX 3060': ('86', 'Ampere', 12000),
        'V100': ('70', 'Volta', 16000),
        'T4': ('75', 'Turing', 15000),
        'RTX 2080': ('75', 'Turing', 8000),
        'RTX 2070': ('75', 'Turing', 8000),
        'RTX 2060': ('75', 'Turing', 6000),
        'GTX 1660': ('75', 'Turing', 6000),
        'GTX 1650': ('75', 'Turing', 4000),
        'GTX 1080': ('61', 'Pascal', 8000),
        'GTX 1070': ('61', 'Pascal', 8000),
        'GTX 1060': ('61', 'Pascal', 6000),
    }
    
    def __init__(self):
        self.gpu_info = None
        self.cuda_available = False
        self._detect_hardware()
    
    def _detect_hardware(self):
        """检测硬件信息"""
        try:
            import torch
            self.cuda_available = torch.cuda.is_available()
            
            if self.cuda_available:
                self.gpu_info = self._get_gpu_info()
        except ImportError:
            print("⚠️  PyTorch not available, GPU detection disabled")
    
    def _get_gpu_info(self) -> Optional[Dict]:
        """获取GPU详细信息"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            if result.returncode == 0:
                line = result.stdout.strip().split('\n')[0]
                gpu_name, vram_mb = line.split(',')
                gpu_name = gpu_name.strip()
                vram_mb = int(float(vram_mb.strip()))
                
                compute_cap, arch, _ = self._identify_gpu(gpu_name)
                
                return {
                    'name': gpu_name,
                    'vram_mb': vram_mb,
                    'compute_capability': compute_cap,
                    'architecture': arch
                }
        except Exception as e:
            print(f"⚠️  Failed to get GPU info: {e}")
        
        return None
    
    def _identify_gpu(self, gpu_name: str) -> Tuple[str, str, int]:
        """识别GPU型号"""
        for model, (cap, arch, min_vram) in self.GPU_COMPUTE_CAPABILITY.items():
            if model.upper() in gpu_name.upper():
                return cap, arch, min_vram
        
        # 未识别的GPU，尝试通过PyTorch获取
        try:
            import torch
            if torch.cuda.is_available():
                major, minor = torch.cuda.get_device_capability(0)
                return f"{major}{minor}", "Unknown", 0
        except:
            pass
        
        return "Unknown", "Unknown", 0
    
    def get_optimized_params(self, model_size_gb: float = 7.0) -> Dict:
        """
        根据硬件获取优化参数
        
        Args:
            model_size_gb: 模型大小（GB）
        
        Returns:
            优化参数字典
        """
        params = {
            'n_gpu_layers': 0,
            'n_ctx': 2048,
            'n_batch': 512,
            'n_threads': 4,
            'use_mmap': True,
            'use_mlock': False,
            'device_info': 'CPU only',
            'rope_freq_base': 10000,
            'rope_freq_scale': 1.0,
        }
        
        if not self.cuda_available or not self.gpu_info:
            return params
        
        vram_mb = self.gpu_info['vram_mb']
        gpu_name = self.gpu_info['name']
        
        # 根据显存大小调整参数
        if vram_mb >= 70000:  # 70GB+ (H100, A100 80G)
            params.update({
                'n_gpu_layers': -1,
                'n_ctx': 8192,
                'n_batch': 1024,
                'n_threads': 8,
                'use_mlock': True,
                'device_info': f'{gpu_name} (High VRAM mode - Optimized for {vram_mb}MB)'
            })
        elif vram_mb >= 40000:  # 40GB+ (A100 40G, A40)
            params.update({
                'n_gpu_layers': -1,
                'n_ctx': 8192,
                'n_batch': 512,
                'n_threads': 8,
                'device_info': f'{gpu_name} (High VRAM mode - {vram_mb}MB)'
            })
        elif vram_mb >= 20000:  # 20GB+ (RTX 4090, 3090, A30)
            params.update({
                'n_gpu_layers': -1,
                'n_ctx': 4096,
                'n_batch': 512,
                'n_threads': 6,
                'device_info': f'{gpu_name} (Normal VRAM mode - {vram_mb}MB)'
            })
        elif vram_mb >= 10000:  # 10GB+ (RTX 3080, 4070)
            params.update({
                'n_gpu_layers': -1,
                'n_ctx': 2048,
                'n_batch': 256,
                'n_threads': 4,
                'device_info': f'{gpu_name} (Normal VRAM mode - {vram_mb}MB)'
            })
        elif vram_mb >= 6000:  # 6GB+ (RTX 3060, 2060)
            estimated_layers = int((vram_mb - 2000) / (model_size_gb * 1024 / 40))
            params.update({
                'n_gpu_layers': max(20, min(estimated_layers, 50)),
                'n_ctx': 2048,
                'n_batch': 128,
                'n_threads': 4,
                'device_info': f'{gpu_name} (Low VRAM mode - Partial offload, {vram_mb}MB)'
            })
        else:  # <6GB
            params.update({
                'n_gpu_layers': 0,
                'n_ctx': 2048,
                'n_batch': 128,
                'n_threads': 4,
                'device_info': f'{gpu_name} (CPU mode - Insufficient VRAM, {vram_mb}MB)'
            })
        
        return params
    
    def get_device_summary(self) -> str:
        """获取设备摘要信息"""
        if not self.cuda_available:
            return "❌ No CUDA GPU detected"
        
        if not self.gpu_info:
            return "⚠️  GPU detected but info unavailable"
        
        info = self.gpu_info
        return (
            f"✅ {info['name']}\n"
            f"   VRAM: {info['vram_mb']} MB\n"
            f"   Architecture: {info['architecture']}\n"
            f"   Compute Capability: {info['compute_capability']}"
        )
    
    def check_llama_cpp_installation(self) -> Dict[str, any]:
        """检查 llama-cpp-python 安装状态"""
        result = {
            'installed': False,
            'version': None,
            'cuda_support': False,
            'cuda_linked': False,
            'architecture': None,
            'issues': []
        }
        
        try:
            import llama_cpp
            result['installed'] = True
            result['version'] = llama_cpp.__version__
            
            # 检查CUDA库链接
            from pathlib import Path
            
            llama_lib_dir = Path(llama_cpp.__file__).parent / 'lib'
            if llama_lib_dir.exists():
                so_files = list(llama_lib_dir.glob("*.so"))
                for so_file in so_files:
                    try:
                        ldd_output = subprocess.run(
                            f"ldd {so_file}",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=5
                        ).stdout
                        
                        if any(lib in ldd_output for lib in ['libcuda', 'libcublas', 'libcudart']):
                            result['cuda_linked'] = True
                            result['cuda_support'] = True
                            
                            # 检查编译架构
                            strings_output = subprocess.run(
                                f"strings {so_file} | grep 'sm_' | head -n 1",
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            ).stdout.strip()
                            
                            if strings_output:
                                result['architecture'] = strings_output
                            break
                    except:
                        pass
            
            if not result['cuda_support']:
                result['issues'].append("CUDA support not detected - llama-cpp-python may not be compiled with CUDA")
            
        except ImportError as e:
            result['issues'].append(f"llama-cpp-python not installed: {e}")
            result['issues'].append("Install with: pip install llama-cpp-python")
        except Exception as e:
            result['issues'].append(f"Error checking installation: {e}")
        
        return result
