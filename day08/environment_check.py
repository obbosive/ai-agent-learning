import sys
import requests
def show_environment():
    print(f"解释器位于{sys.executable}")
    print(f"是否处于虚拟环境：{sys.prefix!=sys.base_prefix}")
    print(f"requests版本：{requests.__version__}")
    print(f"requests位置：{requests.__file__}")

if __name__=="__main__":
    show_environment()