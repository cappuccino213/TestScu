"""
@File : parseConfig.py
@Date : 2021/8/25
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""

import os
import configparser


class Config:
	def __init__(self, config_file='config.ini'):
		self._path = os.path.join(os.getcwd(), config_file)
		if not os.path.exists(self._path):
			raise FileNotFoundError("no such file:{}".format(self._path))
		# ConfigParser支持值的插值，即值可以在被 get() 调用返回之前进行预处理,
		# https://docs.python.org/zh-cn/3/library/configparser.html#interpolation-of-values
		self._config = configparser.ConfigParser(allow_no_value=True)
		self._config.read(self._path, encoding='utf-8')

	# 普通解析，返回string
	def get(self, section, name):
		return self._config.get(section, name)

	# 返回int
	def get_int(self, section, name):
		return self._config.getint(section, name)

	# 返回float
	def get_float(self, section, name):
		return self._config.getfloat(section, name)

	# 返回bool
	def get_bool(self, section, name):
		return self._config.getboolean(section, name)


cfg = Config()

if __name__ == '__main__':
	# print(cfg.get('Network', 'RemoteIP'), cfg.get_int('Network', 'RemotePort'))
	print(cfg.get_bool('API', 'IsOpen'),type(cfg.get_bool('API', 'IsOpen')))
