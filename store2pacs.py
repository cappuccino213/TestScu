"""
@File : store2pacs.py
@Date : 2021/8/25
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""

import os
from pydicom import dcmread
from parseConfig import cfg
from pynetdicom import AE
from pydicom.uid import generate_uid
from datetime import datetime
from common import get_token
from requests import post

"""遍历dcm文件，返回dcm文件list"""


def get_dcm_file(file_path):
	return [file for file in os.listdir(file_path) if file.endswith('.dcm') or file.endswith('.DCM')]


"""读取影像信息，修改影像信息"""


def read_dcm(dcm_file, image_info):
	ds = dcmread(dcm_file)
	# if image_info.get("TransferSyntax"):
	# 	ds.file_meta.TransferSyntaxUID = image_info.get("TransferSyntax")
		# ds.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.4.90'
	# else:
	# 	ds.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'
	if image_info.get("accessionNumber"):
		ds.AccessionNumber = image_info.get("accessionNumber")
	if image_info.get("patientID"):
		ds.PatientID = image_info.get("patientID")
	if image_info.get("name"):  # 中文姓名
		ds.OtherPatientNames = image_info.get("name")
	if image_info.get("nameSpell"):  # 英文姓名
		ds.PatientName = image_info.get("nameSpell")
	if image_info.get("StudyDate"):
		ds.StudyDate = image_info.get("StudyDate")
		ds.AcquisitionDate = image_info.get("StudyDate")
		ds.ContentDate = image_info.get("StudyDate")
	else:
		now_dt = datetime.now().strftime('%Y%m%d')
		ds.StudyDate = now_dt
		ds.AcquisitionDate = now_dt
		ds.ContentDate = now_dt

	if image_info.get("StudyTime"):
		ds.StudyTime = image_info.get("StudyTime")
		ds.AcquisitionTime = image_info.get("StudyTime")
		ds.ContentTime = image_info.get("StudyTime")
	else:
		now_t = datetime.now().strftime('%H%M%S.%f')[0:10]
		ds.StudyTime = now_t
		ds.AcquisitionTime = str(float(now_t) + 8)  # 间隔8秒
		ds.ContentTime = str(float(now_t) + 4)  # 间隔4秒
	# 生成uid
	ds.StudyInstanceUID = generate_uid()
	ds.SeriesInstanceUID = generate_uid()
	ds.SOPInstanceUID = generate_uid()
	return ds


"""获取RIS登记的检查信息"""


def get_order_info():
	if cfg.get_bool('API', 'IsOpen'):
		url = cfg.get('API', 'url')
		header = {'Content-Type': 'application/json',
				  'Authorization': get_token()}
		payload = {'OrganizationCode': cfg.get('API', 'OrganizationCode'),
				   # 'ObservationEndDate': cfg.get('API', 'ObservationEndDate'),
				   'ResultStatus': cfg.get('API', 'ResultStatus')}
		if cfg.get('API', 'ObservationEndDate'):  # 取配置文件中检查时间
			payload['ObservationEndDate'] = cfg.get('API', 'ObservationEndDate')
		else:  # 若没有设置则设置时间为当天
			payload['ObservationEndDate'] = datetime.now().strftime('%Y/%m/%d 0:00:00') + '|' + datetime.now().strftime(
				'%Y/%m/%d %H:%M:%S')
		res = post(url, headers=header, json=payload)
		if res.json()['data']:
			image_dict = res.json()['data']
		else:
			print('未获取到机构{}|检查时间{}的患者登记信息'.format(payload['OrganizationCode'], payload['ObservationEndDate']))
			image_dict = []
	else:
		image_dict = dict(TransferSyntax=cfg.get('StorePACS', 'TransferSyntax'),
						  accessionNumber=cfg.get('DcmInfo', 'accessionNumber'),
						  patientID=cfg.get('DcmInfo', 'patientId'),
						  name=cfg.get('DcmInfo', 'name'),
						  nameSpell=cfg.get('DcmInfo', 'nameSpell'))
	return image_dict


"""发送影像至pacs服务器"""


def send_dcm(ds):
	# 定义本地ae
	ae = AE(ae_title=cfg.get('Network', 'LocalAET'))

	# 添加请求的影像类型
	# ae.add_requested_context(ds['SOPClassUID'].value)
	ae.add_requested_context(ds.file_meta.TransferSyntaxUID)

	#
	ae.remove_requested_context('1.2.840.10008.1.2.1.99')

	# 创建链接
	assoc = ae.associate(cfg.get('Network', 'RemoteIP'), cfg.get_int('Network', 'RemotePort'),
						 ae_title=cfg.get('Network', 'RemoteAET'))

	# 使用C-Store服务发送影像
	if assoc.is_established:
		status = assoc.send_c_store(ds)
		if status:
			# If the storage request succeeded this will be 0x0000
			# print('C-STORE request status: 0x{0:04x}'.format(status.Status))
			print('发送影像{}成功'.format(ds['SOPInstanceUID'].value))
		else:
			print('Connection timed out, was aborted or received invalid response')
		# Release the association
		assoc.release()
	else:
		print('Association rejected, aborted or never connected')


# 具体发送操作
def main():
	# 待发送影像列表
	dcm_list = get_dcm_file(cfg.get('StorePACS', 'DcmPath'))
	# 取影像信息
	image_dict = get_order_info()
	# 发送影像
	if isinstance(image_dict, list):  # 判断获取的影像信息是否批量
		for image_info in image_dict:
			print('获取患者信息acc:{} patientID:{} name:{}'.format(image_info['orderInfo']['accessionNumber'],
															 image_info['orderInfo']['accessionNumber'],
															 image_info['orderInfo']['name']))
			for image in dcm_list:
				image_path = os.path.join(cfg.get('StorePACS', 'DcmPath'), image)
				send_dcm(read_dcm(image_path, image_info.get('orderInfo')))
	else:
		for image in dcm_list:
			image_path = os.path.join(cfg.get('StorePACS', 'DcmPath'), image)
			send_dcm(read_dcm(image_path, image_dict))


if __name__ == "__main__":
	main()
	# image_dict = dict(TransferSyntax=cfg.get('StorePACS', 'TransferSyntax'),
	# 				  accessionNumber=cfg.get('DcmInfo', 'accessionNumber'),
	# 				  patientID=cfg.get('DcmInfo', 'patientId'),
	# 				  name=cfg.get('DcmInfo', 'name'),
	# 				  nameSpell=cfg.get('DcmInfo', 'nameSpell'))
	# read_dcm(r'D:\Python\Project\TestScu\DcmFile\JPEG Lossless1.2.840.10008.1.2.4.70\1.2.392.200036.9123.100.11.12.400001538.2.2019121113163739.dcm',image_dict)