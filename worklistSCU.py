"""
@File : worklistSCU.py
@Date : 2021/8/30
@Author: 九层风（YePing Zhang）
@Contact : yeahcheung213@163.com
"""

from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import _BASIC_WORKLIST_CLASSES
from parseConfig import cfg

MWIF = _BASIC_WORKLIST_CLASSES['ModalityWorklistInformationFind']


# 创建dataset
def create_dataset():
	ds = Dataset()
	ds.ScheduledProcedureStepSequence = [Dataset()]
	item = ds.ScheduledProcedureStepSequence[0]
	item.ScheduledStationAETitle = cfg.get('WorkList', 'LocalAET')
	item.Modality = cfg.get('WorkList', 'Modality')
	if cfg.get('WorkList', 'PatientName'):
		ds.PatientName = cfg.get('WorkList', 'PatientName')
	if cfg.get('WorkList', 'StartDate'):
		item.ScheduledProcedureStepStartDate = cfg.get('WorkList', 'StartDate')
	return ds


# 获取患者列表
def get_order_list(dataset):
	ae = AE()
	ae = ae.add_requested_context(MWIF)
	assoc = ae.associate(cfg.get('WorkList', 'WLIP'), cfg.get_int('WorkList', 'WLPort'),
						 ae_title=cfg.get('WorkList', 'WLAET'))
	if assoc.is_established:
		responses = assoc.send_c_find(dataset, MWIF)
		for (status, identifier) in responses:
			if status:
				print('C-FIND query status: 0x{0:04x}'.format(status.Status))
			else:
				print('Connection timed out, was aborted or received invalid response')

			# Release the association
			assoc.release()
		else:
			print('Association rejected, aborted or never connected')


def main():
	get_order_list(create_dataset())


if __name__ == "__main__":
	main()
