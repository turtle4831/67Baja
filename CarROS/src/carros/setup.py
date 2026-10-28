import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'carros'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='turtle',
    maintainer_email='jakethrun@gmail.com',
    description='Baja car ROS 2 sensor layer',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'dummy_sensor = carros.dummy_sensor:main',
            'joy_servo = carros.joy_servo:main',
        ],
    },
)
