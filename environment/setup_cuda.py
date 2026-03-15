"""
CUDA环境检查和配置脚本
用于验证系统是否支持CUDA加速，并提供配置建议
"""

import torch
import subprocess
import platform
import sys

def check_cuda_availability():
    """检查CUDA是否可用"""
    print("=" * 60)
    print("CUDA环境检查报告")
    print("=" * 60)
    
    # 检查PyTorch是否支持CUDA
    cuda_available = torch.cuda.is_available()
    print(f"PyTorch CUDA支持: {'✓ 可用' if cuda_available else '✗ 不可用'}")
    
    if cuda_available:
        # CUDA版本信息
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"cuDNN版本: {torch.backends.cudnn.version()}")
        
        # GPU信息
        gpu_count = torch.cuda.device_count()
        print(f"GPU数量: {gpu_count}")
        
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"GPU {i}: {gpu_name}")
            print(f"  显存: {gpu_memory:.1f} GB")
            
            # 检查当前显存使用情况
            allocated = torch.cuda.memory_allocated(i) / 1024**3
            cached = torch.cuda.memory_reserved(i) / 1024**3
            print(f"  已分配显存: {allocated:.1f} GB")
            print(f"  缓存显存: {cached:.1f} GB")
    
    return cuda_available

def check_system_info():
    """检查系统信息"""
    print("\n" + "=" * 60)
    print("系统信息")
    print("=" * 60)
    
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"PyTorch版本: {torch.__version__}")
    
    # 内存信息（Windows）
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'], 
                                  capture_output=True, text=True)
            total_memory = int(result.stdout.split('\n')[1].strip()) / (1024**3)
            print(f"系统内存: {total_memory:.1f} GB")
    except:
        print("系统内存: 无法获取")

def provide_recommendations(cuda_available):
    """提供配置建议"""
    print("\n" + "=" * 60)
    print("配置建议")
    print("=" * 60)
    
    if not cuda_available:
        print("⚠️  CUDA不可用，将使用CPU训练")
        print("   建议: 训练速度会很慢，建议使用GPU")
        return
    
    # 获取GPU信息
    if torch.cuda.device_count() > 0:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        print(f"检测到GPU: {gpu_name}")
        print(f"显存大小: {gpu_memory:.1f} GB")
        
        # 针对RTX 3070 Ti的建议
        if "3070" in gpu_name or gpu_memory <= 8:
            print("\n🎯 RTX 3070 Ti (8GB) 配置建议:")
            print("   1. 训练时设置 cache=False (避免内存溢出)")
            print("   2. 建议batch_size <= 16")
            print("   3. 使用mixed precision训练 (torch.cuda.amp)")
            print("   4. 考虑使用gradient accumulation")
            print("   5. 数据加载时设置num_workers=2-4")
            
            # 内存建议
            print("\n💾 内存优化建议:")
            print("   1. 如果系统内存为16GB，建议升级到32GB")
            print("   2. 训练时关闭不必要的程序")
            print("   3. 使用数据增强时注意内存使用")
            print("   4. 定期清理GPU缓存: torch.cuda.empty_cache()")

def main():
    """主函数"""
    try:
        cuda_available = check_cuda_availability()
        check_system_info()
        provide_recommendations(cuda_available)
        
        print("\n" + "=" * 60)
        print("检查完成！")
        print("=" * 60)
        
        if cuda_available:
            print("✅ 系统支持CUDA加速，可以开始训练！")
        else:
            print("⚠️  系统不支持CUDA，将使用CPU训练")
            
    except Exception as e:
        print(f"检查过程中出现错误: {e}")
        print("请确保已正确安装PyTorch和CUDA驱动")

if __name__ == "__main__":
    main()