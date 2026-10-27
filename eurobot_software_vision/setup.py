from setuptools import find_packages, setup

package_name = 'eurobot_software_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Tu Nombre',
    maintainer_email='tu@email.com',
    description='Paquete de visión artificial para Eurobot 2027',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Aquí vinculamos el comando de terminal con el archivo python
            'vision_node = eurobot_software_vision.vision_node:main'
        ],
    },
)
