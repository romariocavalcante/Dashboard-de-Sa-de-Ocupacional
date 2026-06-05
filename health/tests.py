from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import EmployeeRecord


class EmployeeSpreadsheetImportExportTests(TestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.admin = self.user_model.objects.create_user(
			username="admin",
			password="123456",
			is_staff=True,
		)
		self.user = self.user_model.objects.create_user(
			username="user",
			password="123456",
		)

	def test_admin_can_import_csv(self):
		self.client.force_login(self.admin)
		initial_count = EmployeeRecord.objects.count()
		csv_content = (
			"chapa,nome,funcao,secao,dt_inicio,dt_final,dias_afastados,motivo,cid,qtd_atestados\n"
			"1001,Maria,Enfermeira,Saude,2026-03-30,2026-03-30,1,Atestado,C12,3\n"
		)
		file_obj = SimpleUploadedFile("funcionarios.csv", csv_content.encode("utf-8"), content_type="text/csv")

		response = self.client.post(
			reverse("health:importar-funcionarios-planilha"),
			{"planilha": file_obj},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(EmployeeRecord.objects.count(), initial_count + 1)
		record = EmployeeRecord.objects.order_by("-id").first()
		self.assertEqual(record.payload.get("nome"), "Maria")
		self.assertEqual(record.payload.get("funcao"), "Enfermeira")
		self.assertEqual(record.payload.get("qtd_atestados"), 3)

	def test_non_admin_cannot_import(self):
		self.client.force_login(self.user)
		initial_count = EmployeeRecord.objects.count()
		csv_content = "nome,funcao\nJoao,Analista\n"
		file_obj = SimpleUploadedFile("funcionarios.csv", csv_content.encode("utf-8"), content_type="text/csv")

		response = self.client.post(
			reverse("health:importar-funcionarios-planilha"),
			{"planilha": file_obj},
		)

		self.assertEqual(response.status_code, 403)
		self.assertEqual(EmployeeRecord.objects.count(), initial_count)

	def test_admin_can_export_json(self):
		self.client.force_login(self.admin)
		EmployeeRecord.objects.create(payload={"nome": "Ana", "funcao": "Tecnica"}, ativo=True, ordem=0)

		response = self.client.get(reverse("health:exportar-funcionarios-json"))

		self.assertEqual(response.status_code, 200)
		self.assertIn("application/json", response["Content-Type"])
		self.assertIn("Ana", response.content.decode("utf-8"))

	def test_admin_can_export_xml(self):
		self.client.force_login(self.admin)
		EmployeeRecord.objects.create(payload={"nome": "Carlos", "funcao": "Medico"}, ativo=True, ordem=1)

		response = self.client.get(reverse("health:exportar-funcionarios-xml"))

		self.assertEqual(response.status_code, 200)
		self.assertIn("application/xml", response["Content-Type"])
		body = response.content.decode("utf-8")
		self.assertIn("<funcionarios>", body)
		self.assertIn("Carlos", body)
