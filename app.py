"""
IVSURF Volatility Explorer - Vercel Deployment Entry Point
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main terminal
from scripts.ivsurf_retro_terminal import main

if __name__ == "__main__":
    main()
