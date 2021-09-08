"""
@File : common.py
@Date : 2021/8/27
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""


def get_token():
	from requests import post
	header = {'Content-Type': 'application/json'}
	url = "http://192.168.1.18:8709/Token/RetriveInternal"
	payload = {
		"ProductName": "eWordRIS",
		"HospitalCode": "QWYHZYFZX",
		"RequestIP": "192.168.1.56"
	}
	res = post(url, headers=header, json=payload)
	return res.json()['token']


if __name__ == "__main__":
	print(get_token())
