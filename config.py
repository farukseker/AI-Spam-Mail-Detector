import os


env = os.getenv

TEST_USERNAME: str = env('USERNAME')
TEST_PASSWORD: str = env('PASSWORD')
