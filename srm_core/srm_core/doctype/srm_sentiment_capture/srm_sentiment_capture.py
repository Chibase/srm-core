# Copyright (c) 2026, Chibase Consulting and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from srm_core.services.geographic_area import validate_geographic_area_link


class SRMSentimentCapture(Document):
	def validate(self):
		validate_geographic_area_link(self)
