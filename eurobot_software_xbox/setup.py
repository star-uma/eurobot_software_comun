from setuptools import find_packages, setup

package_name = 'eurobot_software_xbox'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/xbox.launch.py']),
        ('share/' + package_name + '/config', ['config/joy_teleop.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Equipo',
    maintainer_email='tu@email.com',
    description='Paquete de control por mando Xbox para Eurobot 2027',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'xbox_teleop_node = eurobot_software_xbox.xbox_teleop:main'
        ],
    },
)