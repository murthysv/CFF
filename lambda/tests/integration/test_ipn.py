"""
npm test -- tests.integration.test_ipn
"""
import unittest
from chalice.config import Config
from chalice.local import LocalGateway
import json
from .constants import FORM_ID, AWS_REGION
from app import app
from tests.integration.baseTestCase import BaseTestCase
from chalicelib.models import Response, PaymentStatusDetailItem
import datetime
from bson.objectid import ObjectId
from .constants import ONE_SCHEMA, ONE_UISCHEMA, ONE_FORMOPTIONS, ONE_FORMDATA
import responses
import mock
from unittest.mock import MagicMock, PropertyMock


class FormIpn(BaseTestCase):
    maxDiff = None

    def setUp(self):
        super(FormIpn, self).setUp()
        self.formId = self.create_form()
        self.edit_form(
            self.formId,
            {
                "schema": ONE_SCHEMA,
                "uiSchema": ONE_UISCHEMA,
                "formOptions": ONE_FORMOPTIONS,
            },
        )

    def send_ipn(self, responseId, body, fail=False):
        response = self.lg.handle_request(
            method="POST",
            path=f"/responses/{responseId}/ipn",
            headers={
                "authorization": "auth",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body=body,
        )
        if fail:
            self.assertEqual(response["statusCode"], 500)
        else:
            self.assertEqual(response["statusCode"], 200, response)
            self.assertEqual(response["body"], "")
        return response["body"]

    @responses.activate
    @mock.patch("boto3.client")
    def test_ipn_verified_success(self, mock_boto_client):
        ses_mock = MagicMock()
        mock_boto_client.return_value = ses_mock
        send_email = PropertyMock()
        ses_mock.send_email = send_email

        responses.add(
            responses.POST,
            "https://www.sandbox.paypal.com/cgi-bin/webscr",
            body="VERIFIED",
            status=200,
        )
        responseId = str(ObjectId())
        response = Response(
            id=ObjectId(responseId),
            form=self.formId,
            date_modified=datetime.datetime.now(),
            date_created=datetime.datetime.now(),
            value={"a": "b", "email": "success@simulator.amazonses.com"},
            paymentInfo={
                "total": 0.5,
                "currency": "USD",
                "items": [
                    {"name": "a", "description": "b", "amount": 0.25, "quantity": 1},
                    {"name": "a2", "description": "b2", "amount": 0.25, "quantity": 1},
                ],
            },
        ).save()
        ipn_value = f"mc_gross=0.50&protection_eligibility=Eligible&address_status=confirmed&item_number1=Base Registration&payer_id=VE2HLZ5ZKU7BE&address_street=123 ABC Street&payment_date=06:42:00 Jun 30, 2018 PDT&payment_status=Completed&charset=windows-1252&address_zip=30022&first_name=Ashwin&mc_fee=0.31&address_country_code=US&address_name=outplayed apps&notify_version=3.9&custom={responseId}&payer_status=unverified&business=aramaswamis-facilitator@gmail.com&address_country=United States&num_cart_items=1&address_city=Johns creek&verify_sign=AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV&payer_email=aramaswamis@gmail.com&txn_id=6TS1068787252245S&payment_type=instant&payer_business_name=outplayed apps&last_name=Ramaswami&address_state=GA&item_name1=Base Registration&receiver_email=aramaswamis-facilitator@gmail.com&payment_fee=0.31&quantity1=1&receiver_id=T4A6C58SP7PP2&txn_type=cart&mc_gross_1=0.50&mc_currency=USD&residence_country=US&test_ipn=1&transaction_subject=&payment_gross=0.50&ipn_track_id=d61ac3d69a842"
        self.send_ipn(responseId, ipn_value)

        response = self.view_response(responseId)

        detail_payment_one = response["payment_status_detail"][0]
        detail_payment_one.pop("date")
        detail_payment_one.pop("date_created")
        detail_payment_one.pop("date_modified")
        self.assertEqual(
            detail_payment_one,
            {
                "currency": "USD",
                "amount": "0.50",
                "method": "paypal_ipn",
                "id": "6TS1068787252245S",
                "_cls": "chalicelib.models.PaymentStatusDetailItem",
            },
        )
        detail_history_one = response["payment_trail"][0]
        detail_history_one.pop("date")
        detail_history_one.pop("date_created")
        detail_history_one.pop("date_modified")
        self.assertEqual(
            detail_history_one,
            {
                "value": {
                    "mc_gross": "0.50",
                    "protection_eligibility": "Eligible",
                    "address_status": "confirmed",
                    "item_number1": "Base Registration",
                    "payer_id": "VE2HLZ5ZKU7BE",
                    "address_street": "123 ABC Street",
                    "payment_date": "06:42:00 Jun 30, 2018 PDT",
                    "payment_status": "Completed",
                    "charset": "windows-1252",
                    "address_zip": "30022",
                    "first_name": "Ashwin",
                    "mc_fee": "0.31",
                    "address_country_code": "US",
                    "address_name": "outplayed apps",
                    "notify_version": "3.9",
                    "custom": responseId,
                    "payer_status": "unverified",
                    "business": "aramaswamis-facilitator@gmail.com",
                    "address_country": "United States",
                    "num_cart_items": "1",
                    "address_city": "Johns creek",
                    "verify_sign": "AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV",
                    "payer_email": "aramaswamis@gmail.com",
                    "txn_id": "6TS1068787252245S",
                    "payment_type": "instant",
                    "payer_business_name": "outplayed apps",
                    "last_name": "Ramaswami",
                    "address_state": "GA",
                    "item_name1": "Base Registration",
                    "receiver_email": "aramaswamis-facilitator@gmail.com",
                    "payment_fee": "0.31",
                    "quantity1": "1",
                    "receiver_id": "T4A6C58SP7PP2",
                    "txn_type": "cart",
                    "mc_gross_1": "0.50",
                    "mc_currency": "USD",
                    "residence_country": "US",
                    "test_ipn": "1",
                    "payment_gross": "0.50",
                    "ipn_track_id": "d61ac3d69a842",
                },
                "method": "paypal_ipn",
                "status": "SUCCESS",
                "id": "6TS1068787252245S",
                "_cls": "chalicelib.models.PaymentTrailItem",
            },
        )
        self.assertTrue(len(response["email_trail"]) > 0)
        self.assertEqual(response["paid"], True)
        self.assertEqual(response["amount_paid"], "0.5")
        mock_boto_client.assert_called_once_with("ses", region_name=AWS_REGION)
        send_email.assert_called_once_with(
            Destination={
                "ToAddresses": ["success@simulator.amazonses.com"],
                "CcAddresses": [],
                "BccAddresses": [],
            },
            Message={
                "Subject": {"Data": "2018-19 BBNJ form", "Charset": "utf-8"},
                "Body": {
                    "Text": {
                        "Data": "![](http://www.chinmayanewyork.org/wp-\ncontent/uploads/2014/08/banner17_ca1.png)\n\n# Confirmation\n\n## 2018-19 Long Island Balavihar Registration Form\n\nThank you for submitting the form. This is a confirmation that we have\nreceived your response.  \n  \nA| b  \n---|---  \nEmail| success@simulator.amazonses.com  \n  \n## Payment Info\n\nItem| Amount| Quantity  \n---|---|---  \na| $0.25| 1  \na2| $0.25| 1  \n  \n **Total Amount: $0.50**  \n  \n  \nWe thank you for your contribution and support.  \nChinmaya Mission New York is a not-for-profit organization exempt from Federal\nIncome tax under section 501 (c) (3). Tax ID: 26-1337001.  \nMay Gurudev's Blessing be with you.\n\n",
                        "Charset": "utf-8",
                    },
                    "Html": {
                        "Data": '<div style="width: 100%;background-color: #eee; margin: 10px 0px;"> <div style="width: 80%;margin: auto; box-shadow: 1px 1px 4px grey;padding: 10px 30px;background: white;"> <img src="http://www.chinmayanewyork.org/wp-content/uploads/2014/08/banner17_ca1.png" width="100%"/> <h1>Confirmation</h1> <h2>2018-19 Long Island Balavihar Registration Form</h2>Thank you for submitting the form. This is a confirmation that we have received your response.<br/> <br/> <table> <tbody> <tr><th>A</th><td>b</td></tr> <tr><th>Email</th><td>success@simulator.amazonses.com</td></tr> </tbody> </table> <h2>Payment Info</h2><table><tr><th>Item</th><th>Amount</th><th>Quantity</th></tr><tr><td>a</td><td>$0.25</td><td>1</td></tr><tr><td>a2</td><td>$0.25</td><td>1</td></tr></table><br/><strong>Total Amount: $0.50</strong><br/><br/><br/>We thank you for your contribution and support.<br/>Chinmaya Mission New York is a not-for-profit organization exempt from Federal Income tax under section 501 (c) (3). Tax ID: 26-1337001.<br/>May Gurudev\'s Blessing be with you.</div> </div>',
                        "Charset": "utf-8",
                    },
                },
            },
            Source="CMTC <ccmt.dev@gmail.com>",
        )

    @responses.activate
    def test_ipn_invalid_fail(self):
        responses.add(
            responses.POST,
            "https://www.sandbox.paypal.com/cgi-bin/webscr",
            body="INVALID",
            status=200,
        )
        responseId = str(ObjectId())
        response = Response(
            id=ObjectId(responseId),
            form=self.formId,
            date_modified=datetime.datetime.now(),
            date_created=datetime.datetime.now(),
            value={"a": "b", "email": "success@simulator.amazonses.com"},
            paymentInfo={
                "total": 0.5,
                "currency": "USD",
                "items": [
                    {"name": "a", "description": "b", "amount": 0.25, "quantity": 1},
                    {"name": "a2", "description": "b2", "amount": 0.25, "quantity": 1},
                ],
            },
        ).save()
        ipn_value = f"mc_gross=0.50&protection_eligibility=Eligible&address_status=confirmed&item_number1=Base Registration&payer_id=VE2HLZ5ZKU7BE&address_street=123 ABC Street&payment_date=06:42:00 Jun 30, 2018 PDT&payment_status=Completed&charset=windows-1252&address_zip=30022&first_name=Ashwin&mc_fee=0.31&address_country_code=US&address_name=outplayed apps&notify_version=3.9&custom={responseId}&payer_status=unverified&business=aramaswamis-facilitator@gmail.com&address_country=United States&num_cart_items=1&address_city=Johns creek&verify_sign=AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV&payer_email=aramaswamis@gmail.com&txn_id=6TS1068787252245S&payment_type=instant&payer_business_name=outplayed apps&last_name=Ramaswami&address_state=GA&item_name1=Base Registration&receiver_email=aramaswamis-facilitator@gmail.com&payment_fee=0.31&quantity1=1&receiver_id=T4A6C58SP7PP2&txn_type=cart&mc_gross_1=0.50&mc_currency=USD&residence_country=US&test_ipn=1&transaction_subject=&payment_gross=0.50&ipn_track_id=d61ac3d69a842"
        response = self.send_ipn(responseId, ipn_value, fail=True)
        self.assertIn("Rejected by PayPal", response)

        response = self.view_response(responseId)

        self.assertTrue("payment_status_detail" not in response)
        self.assertEqual(len(response["payment_trail"]), 1)
        detail_history_one = response["payment_trail"][0]
        detail_history_one.pop("date")
        # detail_history_one.pop("date_created")
        # detail_history_one.pop("date_modified")
        self.assertEqual(
            detail_history_one,
            {
                "value": {
                    "mc_gross": "0.50",
                    "protection_eligibility": "Eligible",
                    "address_status": "confirmed",
                    "item_number1": "Base Registration",
                    "payer_id": "VE2HLZ5ZKU7BE",
                    "address_street": "123 ABC Street",
                    "payment_date": "06:42:00 Jun 30, 2018 PDT",
                    "payment_status": "Completed",
                    "charset": "windows-1252",
                    "address_zip": "30022",
                    "first_name": "Ashwin",
                    "mc_fee": "0.31",
                    "address_country_code": "US",
                    "address_name": "outplayed apps",
                    "notify_version": "3.9",
                    "custom": responseId,
                    "payer_status": "unverified",
                    "business": "aramaswamis-facilitator@gmail.com",
                    "address_country": "United States",
                    "num_cart_items": "1",
                    "address_city": "Johns creek",
                    "verify_sign": "AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV",
                    "payer_email": "aramaswamis@gmail.com",
                    "txn_id": "6TS1068787252245S",
                    "payment_type": "instant",
                    "payer_business_name": "outplayed apps",
                    "last_name": "Ramaswami",
                    "address_state": "GA",
                    "item_name1": "Base Registration",
                    "receiver_email": "aramaswamis-facilitator@gmail.com",
                    "payment_fee": "0.31",
                    "quantity1": "1",
                    "receiver_id": "T4A6C58SP7PP2",
                    "txn_type": "cart",
                    "mc_gross_1": "0.50",
                    "mc_currency": "USD",
                    "residence_country": "US",
                    "test_ipn": "1",
                    "payment_gross": "0.50",
                    "ipn_track_id": "d61ac3d69a842",
                },
                "method": "paypal_ipn",
                "status": "ERROR",
                "id": "Rejected by PayPal: https://www.sandbox.paypal.com/cgi-bin/webscr",
                "_cls": "chalicelib.models.PaymentTrailItem",
            },
        )
        self.assertTrue("email_trail" not in response)
        self.assertEqual(response["paid"], False)
        self.assertEqual(response["amount_paid"], "0")

    @responses.activate
    def test_ipn_no_txn_id(self):
        responses.add(
            responses.POST,
            "https://www.sandbox.paypal.com/cgi-bin/webscr",
            body="VERIFIED",
            status=200,
        )
        responseId = str(ObjectId())
        response = Response(
            id=ObjectId(responseId),
            form=self.formId,
            date_modified=datetime.datetime.now(),
            date_created=datetime.datetime.now(),
            value={"a": "b", "email": "success@simulator.amazonses.com"},
            paymentInfo={
                "total": 0.5,
                "currency": "USD",
                "items": [
                    {"name": "a", "description": "b", "amount": 0.25, "quantity": 1},
                    {"name": "a2", "description": "b2", "amount": 0.25, "quantity": 1},
                ],
            },
        ).save()
        ipn_value = f"mc_gross=0.50&protection_eligibility=Eligible&address_status=confirmed&item_number1=Base Registration&payer_id=VE2HLZ5ZKU7BE&address_street=123 ABC Street&payment_date=06:42:00 Jun 30, 2018 PDT&payment_status=Completed&charset=windows-1252&address_zip=30022&first_name=Ashwin&mc_fee=0.31&address_country_code=US&address_name=outplayed apps&notify_version=3.9&custom={responseId}&payer_status=unverified&business=aramaswamis-facilitator@gmail.com&address_country=United States&num_cart_items=1&address_city=Johns creek&verify_sign=AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV&payer_email=aramaswamis@gmail.com&payment_type=instant&payer_business_name=outplayed apps&last_name=Ramaswami&address_state=GA&item_name1=Base Registration&receiver_email=aramaswamis-facilitator@gmail.com&payment_fee=0.31&quantity1=1&receiver_id=T4A6C58SP7PP2&txn_type=cart&mc_gross_1=0.50&mc_currency=USD&residence_country=US&test_ipn=1&transaction_subject=&payment_gross=0.50&ipn_track_id=d61ac3d69a842"
        response = self.send_ipn(responseId, ipn_value, fail=True)
        self.assertIn("No IPN transaction ID.", response)

        response = self.view_response(responseId)

        self.assertTrue("payment_status_detail" not in response)
        self.assertEqual(len(response["payment_trail"]), 1)
        detail_history_one = response["payment_trail"][0]
        detail_history_one.pop("date")
        # detail_history_one.pop("date_created")
        # detail_history_one.pop("date_modified")
        self.assertEqual(
            detail_history_one,
            {
                "value": {
                    "mc_gross": "0.50",
                    "protection_eligibility": "Eligible",
                    "address_status": "confirmed",
                    "item_number1": "Base Registration",
                    "payer_id": "VE2HLZ5ZKU7BE",
                    "address_street": "123 ABC Street",
                    "payment_date": "06:42:00 Jun 30, 2018 PDT",
                    "payment_status": "Completed",
                    "charset": "windows-1252",
                    "address_zip": "30022",
                    "first_name": "Ashwin",
                    "mc_fee": "0.31",
                    "address_country_code": "US",
                    "address_name": "outplayed apps",
                    "notify_version": "3.9",
                    "custom": responseId,
                    "payer_status": "unverified",
                    "business": "aramaswamis-facilitator@gmail.com",
                    "address_country": "United States",
                    "num_cart_items": "1",
                    "address_city": "Johns creek",
                    "verify_sign": "AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV",
                    "payer_email": "aramaswamis@gmail.com",
                    "payment_type": "instant",
                    "payer_business_name": "outplayed apps",
                    "last_name": "Ramaswami",
                    "address_state": "GA",
                    "item_name1": "Base Registration",
                    "receiver_email": "aramaswamis-facilitator@gmail.com",
                    "payment_fee": "0.31",
                    "quantity1": "1",
                    "receiver_id": "T4A6C58SP7PP2",
                    "txn_type": "cart",
                    "mc_gross_1": "0.50",
                    "mc_currency": "USD",
                    "residence_country": "US",
                    "test_ipn": "1",
                    "payment_gross": "0.50",
                    "ipn_track_id": "d61ac3d69a842",
                },
                "method": "paypal_ipn",
                "status": "ERROR",
                "id": "No IPN transaction ID.",
                "_cls": "chalicelib.models.PaymentTrailItem",
            },
        )
        self.assertTrue("email_trail" not in response)
        self.assertEqual(response["paid"], False)
        self.assertEqual(response["amount_paid"], "0")

    @responses.activate
    @mock.patch("boto3.client")
    def test_ipn_refund(self, mock_boto_client):
        ses_mock = MagicMock()
        mock_boto_client.return_value = ses_mock
        send_email = PropertyMock()
        ses_mock.send_email = send_email

        responses.add(
            responses.POST,
            "https://www.sandbox.paypal.com/cgi-bin/webscr",
            body="VERIFIED",
            status=200,
        )
        responseId = str(ObjectId())
        response = Response(
            id=ObjectId(responseId),
            form=self.formId,
            date_modified=datetime.datetime.now(),
            date_created=datetime.datetime.now(),
            value={"a": "b", "email": "success@simulator.amazonses.com"},
            paymentInfo={
                "total": 0.5,
                "currency": "USD",
                "items": [
                    {"name": "a", "description": "b", "amount": 0.25, "quantity": 1},
                    {"name": "a2", "description": "b2", "amount": 0.25, "quantity": 1},
                ],
            },
            payment_status_detail=[
                PaymentStatusDetailItem(
                    amount="1080.00",
                    method="paypal_ipn",
                    currency="USD",
                    id="id1",
                    date=datetime.datetime.now(),
                )
            ],
            paid=True,
            amount_paid="1080.0",
        ).save()
        ipn_value = f"mc_gross=-1080.00&protection_eligibility=Eligible&item_number1=Double Room&payer_id=A4CSL993V3BDG&address_street=1 Main St&payment_date=07:43:04 Jun 23, 2019 PDT&payment_status=Refunded&charset=windows-1252&address_zip=95131&mc_shipping=0.00&mc_handling=0.00&first_name=test&mc_fee=-31.32&address_country_code=US&address_name=test buyer&notify_version=3.9&reason_code=refund&custom={responseId}&business=aramaswamis-facilitator@gmail.com&address_country=United States&mc_handling1=0.00&address_city=San Jose&verify_sign=Ajpb2sm-lsDSWA5XwZfLh0PpsG6IAYl-yqrJx2GLHimSQ3aPkkfr3i2Y&payer_email=aramaswamis-buyer@gmail.com&mc_shipping1=0.00&tax1=0.00&parent_txn_id=23X19291EC9014330&txn_id=69B89632XK721821J&payment_type=instant&last_name=buyer&address_state=CA&item_name1=Double Room ($1200/person)&receiver_email=aramaswamis-facilitator@gmail.com&payment_fee=-31.32&shipping_discount=0.00&quantity1=1&receiver_id=T4A6C58SP7PP2&insurance_amount=0.00&discount=120.00&mc_gross_1=1200.00&mc_currency=USD&residence_country=US&test_ipn=1&shipping_method=Default&transaction_subject=&payment_gross=-1080.00&ipn_track_id=539cae4d23348"
        response = self.send_ipn(responseId, ipn_value)

        response = self.view_response(responseId)
        self.assertTrue("payment_status_detail" in response)

        self.assertEqual(len(response["payment_trail"]), 1)
        detail_history_one = response["payment_trail"][0]
        detail_history_one.pop("date")

        # TODO: why do these two not exist?
        detail_history_one.pop("date_created")
        detail_history_one.pop("date_modified")
        self.assertEqual(
            detail_history_one,
            {
                "value": {
                    "mc_gross": "-1080.00",
                    "protection_eligibility": "Eligible",
                    "item_number1": "Double Room",
                    "payer_id": "A4CSL993V3BDG",
                    "address_street": "1 Main St",
                    "payment_date": "07:43:04 Jun 23, 2019 PDT",
                    "payment_status": "Refunded",
                    "charset": "windows-1252",
                    "address_zip": "95131",
                    "mc_shipping": "0.00",
                    "mc_handling": "0.00",
                    "first_name": "test",
                    "mc_fee": "-31.32",
                    "address_country_code": "US",
                    "address_name": "test buyer",
                    "notify_version": "3.9",
                    "reason_code": "refund",
                    "custom": responseId,
                    "business": "aramaswamis-facilitator@gmail.com",
                    "address_country": "United States",
                    "mc_handling1": "0.00",
                    "address_city": "San Jose",
                    "verify_sign": "Ajpb2sm-lsDSWA5XwZfLh0PpsG6IAYl-yqrJx2GLHimSQ3aPkkfr3i2Y",
                    "payer_email": "aramaswamis-buyer@gmail.com",
                    "mc_shipping1": "0.00",
                    "tax1": "0.00",
                    "parent_txn_id": "23X19291EC9014330",
                    "txn_id": "69B89632XK721821J",
                    "payment_type": "instant",
                    "last_name": "buyer",
                    "address_state": "CA",
                    "item_name1": "Double Room ($1200/person)",
                    "receiver_email": "aramaswamis-facilitator@gmail.com",
                    "payment_fee": "-31.32",
                    "shipping_discount": "0.00",
                    "quantity1": "1",
                    "receiver_id": "T4A6C58SP7PP2",
                    "insurance_amount": "0.00",
                    "discount": "120.00",
                    "mc_gross_1": "1200.00",
                    "mc_currency": "USD",
                    "residence_country": "US",
                    "test_ipn": "1",
                    "shipping_method": "Default",
                    "payment_gross": "-1080.00",
                    "ipn_track_id": "539cae4d23348",
                },
                "method": "paypal_ipn",
                "status": "SUCCESS",
                "id": "69B89632XK721821J",
                "_cls": "chalicelib.models.PaymentTrailItem",
            },
        )

        self.assertTrue("email_trail" in response)
        self.assertEqual(len(response["email_trail"]), 1)
        self.assertEqual(response["paid"], False)
        self.assertEqual(response["amount_paid"], "0.0")

        mock_boto_client.assert_called_once_with("ses", region_name=AWS_REGION)
        send_email.assert_called_once_with(
            Destination={
                "ToAddresses": ["success@simulator.amazonses.com"],
                "CcAddresses": [],
                "BccAddresses": [],
            },
            Message={
                "Subject": {"Data": "2018-19 BBNJ form", "Charset": "utf-8"},
                "Body": {
                    "Text": {
                        "Data": "![](http://www.chinmayanewyork.org/wp-\ncontent/uploads/2014/08/banner17_ca1.png)\n\n# Confirmation\n\n## 2018-19 Long Island Balavihar Registration Form\n\nThank you for submitting the form. This is a confirmation that we have\nreceived your response.  \n  \nA| b  \n---|---  \nEmail| success@simulator.amazonses.com  \n  \n## Payment Info\n\nItem| Amount| Quantity  \n---|---|---  \na| $0.25| 1  \na2| $0.25| 1  \n  \n **Total Amount: $0.50**  \n  \n  \nWe thank you for your contribution and support.  \nChinmaya Mission New York is a not-for-profit organization exempt from Federal\nIncome tax under section 501 (c) (3). Tax ID: 26-1337001.  \nMay Gurudev's Blessing be with you.\n\n",
                        "Charset": "utf-8",
                    },
                    "Html": {
                        "Data": '<div style="width: 100%;background-color: #eee; margin: 10px 0px;"> <div style="width: 80%;margin: auto; box-shadow: 1px 1px 4px grey;padding: 10px 30px;background: white;"> <img src="http://www.chinmayanewyork.org/wp-content/uploads/2014/08/banner17_ca1.png" width="100%"/> <h1>Confirmation</h1> <h2>2018-19 Long Island Balavihar Registration Form</h2>Thank you for submitting the form. This is a confirmation that we have received your response.<br/> <br/> <table> <tbody> <tr><th>A</th><td>b</td></tr> <tr><th>Email</th><td>success@simulator.amazonses.com</td></tr> </tbody> </table> <h2>Payment Info</h2><table><tr><th>Item</th><th>Amount</th><th>Quantity</th></tr><tr><td>a</td><td>$0.25</td><td>1</td></tr><tr><td>a2</td><td>$0.25</td><td>1</td></tr></table><br/><strong>Total Amount: $0.50</strong><br/><br/><br/>We thank you for your contribution and support.<br/>Chinmaya Mission New York is a not-for-profit organization exempt from Federal Income tax under section 501 (c) (3). Tax ID: 26-1337001.<br/>May Gurudev\'s Blessing be with you.</div> </div>',
                        "Charset": "utf-8",
                    },
                },
            },
            Source="CMTC <ccmt.dev@gmail.com>",
        )
    
    @responses.activate
    def test_ipn_subscr_failed(self):
        responses.add(
            responses.POST,
            "https://www.sandbox.paypal.com/cgi-bin/webscr",
            body="VERIFIED",
            status=200,
        )
        responseId = str(ObjectId())
        response = Response(
            id=ObjectId(responseId),
            form=self.formId,
            date_modified=datetime.datetime.now(),
            date_created=datetime.datetime.now(),
            value={"a": "b", "email": "success@simulator.amazonses.com"},
            paymentInfo={
                "total": 0.5,
                "currency": "USD",
                "items": [
                    {"name": "a", "description": "b", "amount": 0.25, "quantity": 1},
                    {"name": "a2", "description": "b2", "amount": 0.25, "quantity": 1},
                ],
            },
        ).save()
        ipn_value = f"mc_gross=0.50&protection_eligibility=Eligible&address_status=confirmed&item_number1=Base Registration&payer_id=VE2HLZ5ZKU7BE&address_street=123 ABC Street&payment_date=06:42:00 Jun 30, 2018 PDT&payment_status=Completed&charset=windows-1252&address_zip=30022&first_name=Ashwin&mc_fee=0.31&address_country_code=US&address_name=outplayed apps&notify_version=3.9&custom={responseId}&payer_status=unverified&business=aramaswamis-facilitator@gmail.com&address_country=United States&num_cart_items=1&address_city=Johns creek&verify_sign=AWkT50gtrA0iXnh55b939tXXlAFYAfxG.wdPFrayvThp7Tw1hro.K3JV&payer_email=aramaswamis@gmail.com&payment_type=instant&payer_business_name=outplayed apps&last_name=Ramaswami&address_state=GA&item_name1=Base Registration&receiver_email=aramaswamis-facilitator@gmail.com&payment_fee=0.31&quantity1=1&receiver_id=T4A6C58SP7PP2&txn_type=subscr_failed&mc_gross_1=0.50&mc_currency=USD&residence_country=US&test_ipn=1&transaction_subject=&payment_gross=0.50&ipn_track_id=d61ac3d69a842"
        response = self.send_ipn(responseId, ipn_value, fail=True)

        response = self.view_response(responseId)

        self.assertTrue("payment_status_detail" not in response)
        self.assertEqual(len(response["payment_trail"]), 1)
        detail_history_one = response["payment_trail"][0]
        detail_history_one.pop("date")
        self.assertEqual(
            detail_history_one["status"], "ERROR"
        )
        self.assertEqual(
            detail_history_one["id"], "txn_type is not supported and must be manually handled."
        )