from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testing import (
    create_user_from_evecharacter,
    json_response_to_dict,
    json_response_to_python,
)

from .. import views
from ..app_settings import (
    STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES,
    STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES,
)
from ..models import Owner, PocoDetails, Structure, Webhook
from .testdata import create_structures, load_entities, load_entity, set_owner_character

MODULE_PATH = "structures.views"


class TestStructureList(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        create_structures()

    def test_should_have_access_to_main_view(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        # when
        request = self.factory.get(reverse("structures:main"))
        request.user = user
        response = views.main(request)
        # then
        self.assertEqual(response.status_code, 200)

    # TODO: This tests fails on sqlite, re-enable it with mysql
    # def test_should_return_summary_data(self):
    #     # given
    #     user, _ = set_owner_character(character_id=1001)
    #     user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
    #     # when
    #     request = self.factory.get(reverse("structures:structure_summary_data"))
    #     request.user = user
    #     response = views.structure_summary_data(request)
    #     # then
    #     self.assertEqual(response.status_code, 200)
    #     data = json_response_to_dict(response)
    #     obj = data[2001]
    #     self.assertEqual(obj["corporation_name"], "Wayne Technologies")
    #     self.assertEqual(obj["alliance_name"], "Wayne Enterprises")
    #     self.assertEqual(obj["citadel_count"], 1)
    #     self.assertEqual(obj["ec_count"], 0)
    #     self.assertEqual(obj["refinery_count"], 1)
    #     self.assertEqual(obj["other_count"], 0)
    #     self.assertEqual(obj["poco_count"], 4)
    #     self.assertEqual(obj["starbase_count"], 3)
    #     self.assertEqual(obj["total"], 9)


class TestStructureListSpecial(TestCase):
    def test_should_show_empty_list(self):
        # given
        load_entity(EveCharacter)
        user, _ = create_user_from_evecharacter(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        # when
        request = RequestFactory().get(reverse("structures:main"))
        request.user = user
        response = views.main(request)
        # then
        self.assertEqual(response.status_code, 200)


class TestStructureListDataPermissions(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        create_structures()

    def _structure_list_data_view(self, user) -> dict:
        """helper method:  makes the request to the view
        and returns response as dict for the given user
        """
        request = self.factory.get(reverse("structures:structure_list_data"))
        request.user = user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)
        return json_response_to_dict(response, "structure_id")

    def test_should_show_no_structures(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), set())

    def test_should_show_own_corporation_only_1(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_own_corporation_only_2(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), {1000000000003})

    def test_should_show_own_alliance_only_1(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_alliance_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,  # only for alliance
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_own_alliance_only_2(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_alliance_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(set(structure_ids), {1000000000003})

    def test_should_show_all_structures(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", user
        )
        # when
        structure_ids = self._structure_list_data_view(user).keys()
        # then
        self.assertSetEqual(
            set(structure_ids),
            {
                1000000000001,
                1000000000002,
                1000000000003,  # only for all
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

    def test_should_show_unanchoring_status(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_unanchoring_status", user
        )
        # when
        data = self._structure_list_data_view(user)
        # then
        structure = data[1000000000003]
        self.assertIn("Unanchoring until", structure["state_details"])

    def test_should_not_show_unanchoring_status(self):
        # given
        user, _ = set_owner_character(character_id=1011)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_corporation_structures", user
        )
        # when
        data = self._structure_list_data_view(user)
        # then
        structure = data[1000000000003]
        self.assertNotIn("Unanchoring until", structure["state_details"])


class TestStructureListFilters(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_structures()
        cls.user, cls.owner = set_owner_character(character_id=1001)
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.basic_access", cls.user
        )
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", cls.user
        )
        cls.factory = RequestFactory()

    @patch(MODULE_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", True)
    def test_default_filter_enabled(self):
        request = self.factory.get(reverse("structures:index"))
        request.user = self.user
        response = views.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list?tags=tag_a")

    @patch(MODULE_PATH + ".STRUCTURES_DEFAULT_TAGS_FILTER_ENABLED", False)
    def test_default_filter_disabled(self):
        request = self.factory.get(reverse("structures:index"))
        request.user = self.user
        response = views.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/structures/list")

    def test_list_filter_by_tag_1(self):
        # no filter
        request = self.factory.get(
            "{}".format(reverse("structures:structure_list_data"))
        )
        request.user = self.user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response, key="structure_id")
        self.assertSetEqual(
            set(data.keys()),
            {
                1000000000001,
                1000000000002,
                1000000000003,
                1200000000003,
                1200000000004,
                1200000000005,
                1200000000006,
                1300000000001,
                1300000000002,
                1300000000003,
            },
        )

        # filter for tag_c
        request = self.factory.get(
            "{}?tags=tag_c".format(reverse("structures:structure_list_data"))
        )
        request.user = self.user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response, key="structure_id")
        self.assertSetEqual(set(data.keys()), {1000000000002, 1000000000003})

        # filter for tag_b
        request = self.factory.get(
            "{}?tags=tag_b".format(reverse("structures:structure_list_data"))
        )
        request.user = self.user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response, key="structure_id")
        self.assertSetEqual(set(data.keys()), {1000000000003})

        # filter for tag_c, tag_b
        request = self.factory.get(
            "{}?tags=tag_c,tag_b".format(reverse("structures:structure_list_data"))
        )
        request.user = self.user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)

        data = json_response_to_dict(response, key="structure_id")
        self.assertSetEqual(set(data.keys()), {1000000000002, 1000000000003})

    def test_call_with_raw_tags(self):
        request = self.factory.get(
            "{}?tags=tag_c,tag_b".format(reverse("structures:main"))
        )
        request.user = self.user
        response = views.main(request)
        self.assertEqual(response.status_code, 200)

    def test_set_tags_filter(self):
        request = self.factory.post(
            reverse("structures:main"),
            data={
                "tag_b": True,
                "tag_c": True,
            },
        )
        request.user = self.user
        response = views.main(request)
        self.assertEqual(response.status_code, 302)
        parts = urlparse(response.url)
        path = parts[2]
        query_dict = parse_qs(parts[4])
        self.assertEqual(path, reverse("structures:main"))
        self.assertIn("tags", query_dict)
        params = query_dict["tags"][0].split(",")
        self.assertSetEqual(set(params), {"tag_c", "tag_b"})


class TestStructurePowerModes(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_entities()

    def setUp(self):
        create_structures(dont_load_entities=True)
        self.user, self.owner = set_owner_character(character_id=1001)
        AuthUtils.add_permission_to_user_by_name("structures.basic_access", self.user)
        AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", self.user
        )

    def display_data_for_structure(self, structure_id: int):
        request = self.factory.get(reverse("structures:structure_list_data"))
        request.user = self.user
        response = views.structure_list_data(request)
        self.assertEqual(response.status_code, 200)

        data = json_response_to_python(response)
        for row in data:
            if row["structure_id"] == structure_id:
                return row

        return None

    def test_full_power(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = now() + timedelta(hours=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Full Power")
        self.assertEqual(
            parse_datetime(my_structure["fuel_expires_at"]["timestamp"]),
            structure.fuel_expires_at,
        )
        self.assertIn("Full Power", my_structure["last_online_at"]["display"])

    def test_low_power(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = now() - timedelta(days=3)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Low Power")
        self.assertEqual(
            parse_datetime(my_structure["last_online_at"]["timestamp"]),
            structure.last_online_at,
        )
        self.assertIn("Low Power", my_structure["fuel_expires_at"]["display"])

    def test_abandoned(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = now() - timedelta(days=7, seconds=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Abandoned")
        self.assertIn("Abandoned", my_structure["fuel_expires_at"]["display"])
        self.assertIn("Abandoned", my_structure["last_online_at"]["display"])

    def test_maybe_abandoned(self):
        structure_id = 1000000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.last_online_at = None
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "Abandoned?")
        self.assertIn("Abandoned?", my_structure["fuel_expires_at"]["display"])
        self.assertIn("Abandoned?", my_structure["last_online_at"]["display"])

    def test_poco(self):
        structure_id = 1200000000003
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertIn("-", my_structure["fuel_expires_at"]["display"])
        self.assertIn("-", my_structure["last_online_at"]["display"])

    def test_starbase_online(self):
        structure_id = 1300000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = now() + timedelta(hours=1)
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertEqual(
            parse_datetime(my_structure["fuel_expires_at"]["timestamp"]),
            structure.fuel_expires_at,
        )
        self.assertIn("-", my_structure["last_online_at"]["display"])

    def test_starbase_offline(self):
        structure_id = 1300000000001
        structure = Structure.objects.get(id=structure_id)
        structure.fuel_expires_at = None
        structure.save()
        my_structure = self.display_data_for_structure(structure_id)
        self.assertEqual(my_structure["power_mode_str"], "")
        self.assertIn("-", my_structure["fuel_expires_at"]["display"])
        self.assertIn("-", my_structure["last_online_at"]["display"])


class TestAddStructureOwner(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_entities([EveCorporationInfo, EveAllianceInfo, EveCharacter, Webhook])
        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        cls.character = cls.character_ownership.character
        cls.factory = RequestFactory()

    def _add_structure_owner(self, token=None, user=None):
        # given
        request = self.factory.get(reverse("structures:add_structure_owner"))
        if not user:
            user = self.user
        if not token:
            token = user.token_set.first()
        request.user = user
        request.token = token
        middleware = SessionMiddleware()
        middleware.process_request(request)
        orig_view = views.add_structure_owner.__wrapped__.__wrapped__.__wrapped__
        # when
        return orig_view(request, token)

    @patch(MODULE_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", True)
    @patch(MODULE_PATH + ".tasks.update_all_for_owner")
    @patch(MODULE_PATH + ".notify_admins")
    @patch(MODULE_PATH + ".messages_plus")
    def test_should_add_new_structure_owner_and_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        response = self._add_structure_owner()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertTrue(mock_notify_admins.called)
        owner = Owner.objects.first()
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertEqual(owner.webhooks.first().name, "Test Webhook 1")
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(MODULE_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(MODULE_PATH + ".tasks.update_all_for_owner")
    @patch(MODULE_PATH + ".notify_admins")
    @patch(MODULE_PATH + ".messages_plus")
    def test_should_add_character_to_existing_structure_owner_and_reactive(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        owner = Owner.objects.create(
            corporation=EveCorporationInfo.objects.get(corporation_id=2102),
            is_active=False,
        )
        _, character_ownership_1011 = create_user_from_evecharacter(
            1011,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        owner.add_character(character_ownership_1011)
        user_1102, character_ownership_1102 = create_user_from_evecharacter(
            1102,
            permissions=["structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        # when
        response = self._add_structure_owner(user=user_1102)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_update_all_for_owner.delay.called)
        owner.refresh_from_db()
        self.assertSetEqual(
            {character_ownership_1011.pk, character_ownership_1102.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertTrue(owner.is_active)

    @patch(MODULE_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(MODULE_PATH + ".tasks.update_all_for_owner")
    @patch(MODULE_PATH + ".notify_admins")
    @patch(MODULE_PATH + ".messages_plus")
    def test_should_add_new_structure_owner_and_not_notify_admins(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # when
        response = self._add_structure_owner()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        owner = Owner.objects.first()
        self.assertSetEqual(
            {self.character_ownership.pk},
            set(owner.characters.values_list("character_ownership", flat=True)),
        )
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_notify_admins.called)
        self.assertTrue(mock_update_all_for_owner.delay.called)

    @patch(MODULE_PATH + ".STRUCTURES_ADMIN_NOTIFICATIONS_ENABLED", False)
    @patch(MODULE_PATH + ".tasks.update_all_for_owner")
    @patch(MODULE_PATH + ".notify_admins")
    @patch(MODULE_PATH + ".messages_plus")
    def test_should_add_structure_owner_with_no_default_webhook(
        self, mock_messages, mock_notify_admins, mock_update_all_for_owner
    ):
        # given
        Webhook.objects.filter(name="Test Webhook 1").update(is_default=False)
        # when
        response = self._add_structure_owner()
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.info.called)
        self.assertFalse(mock_notify_admins.called)
        my_owner = Owner.objects.get(
            characters__character_ownership=self.character_ownership
        )
        self.assertIsNone(my_owner.webhooks.first())
        self.assertTrue(mock_update_all_for_owner.delay.called)

        # webhook.is_default = True
        # webhook.save()

    @patch(MODULE_PATH + ".messages_plus")
    def test_should_report_error_when_token_does_not_belong_to_user(
        self, mock_messages
    ):
        # given
        other_user, _ = create_user_from_evecharacter(
            1011,
            permissions=["structures.basic_access", "structures.add_structure_owner"],
            scopes=Owner.get_esi_scopes(),
        )
        # when
        my_token = other_user.token_set.first()
        response = self._add_structure_owner(token=my_token)
        # then
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("structures:index"))
        self.assertTrue(mock_messages.error.called)


class TestStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_structures()
        my_user, _ = set_owner_character(character_id=1001)
        AuthUtils.add_permission_to_user_by_name("structures.basic_access", my_user)
        cls.factory = RequestFactory()

    def test_view_service_status_ok(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = True
            owner.assets_last_update_at = now()
            owner.assets_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 200)

    def test_view_service_status_fail_structures(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = None
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = True
            owner.assets_last_update_at = now()
            owner.assets_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)

    def test_view_service_status_fail_notifications(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = None
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = True
            owner.assets_last_update_at = now()
            owner.assets_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)

    def test_view_service_status_fail_forwarding(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = None
            owner.assets_last_update_at = now()
            owner.assets_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)

    def test_view_service_status_fail_assets(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now() - timedelta(
                minutes=STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES + 1
            )
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = True
            owner.assets_last_update_at = now()
            owner.assets_last_update_ok = None
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)

    def test_view_service_status_fail_notifications_2(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now() - timedelta(
                minutes=STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES + 1
            )
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now()
            owner.forwarding_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)

    def test_view_service_status_fail_forwarding_2(self):
        for owner in Owner.objects.filter(is_included_in_service_status=True):
            owner.structures_last_update_at = now()
            owner.structures_last_update_ok = True
            owner.notifications_last_update_at = now()
            owner.notifications_last_update_ok = True
            owner.forwarding_last_update_at = now() - timedelta(
                minutes=STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES + 1
            )
            owner.forwarding_last_update_ok = True
            owner.save()

        request = self.factory.get(reverse("structures:service_status"))
        response = views.service_status(request)
        self.assertEqual(response.status_code, 500)


class TestPocoList(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_structures()
        cls.user, cls.owner = set_owner_character(character_id=1001)
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.basic_access", cls.user
        )
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_all_structures", cls.user
        )
        cls.factory = RequestFactory()

    def test_should_return_all_pocos(self):
        # given
        request = self.factory.get(reverse("structures:poco_list_data"))
        request.user = self.user
        self.owner.are_pocos_public = True
        self.owner.save()
        # when
        response = views.poco_list_data(request)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertSetEqual(
            set(data.keys()),
            {1200000000003, 1200000000004, 1200000000005, 1200000000006},
        )
        obj = data[1200000000003]
        self.assertEqual(obj["region"], "Heimatar")
        self.assertEqual(obj["solar_system"], "Amamake")
        self.assertEqual(obj["planet"], "Amamake V")
        self.assertEqual(obj["planet_type_name"], "Barren")
        self.assertEqual(obj["space_type"], "lowsec")

    def test_should_return_no_pocos(self):
        # given
        request = self.factory.get(reverse("structures:poco_list_data"))
        request.user = self.user
        self.owner.are_pocos_public = False
        self.owner.save()
        # when
        response = views.poco_list_data(request)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertFalse(data)


class TestStructureFittingModal(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        create_structures()

    def test_should_have_access_to_fitting(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        user = AuthUtils.add_permission_to_user_by_name(
            "structures.view_structure_fit", user
        )
        # when
        request = self.factory.get(
            reverse("structures:structure_details", args=[1000000000001])
        )
        request.user = user
        response = views.structure_details(request, 1000000000001)
        # then
        self.assertEqual(response.status_code, 200)

    def test_should_not_have_access_to_fitting(self):
        # given
        user, _ = set_owner_character(character_id=1001)
        user = AuthUtils.add_permission_to_user_by_name("structures.basic_access", user)
        # when
        request = self.factory.get(
            reverse("structures:structure_details", args=[1000000000001])
        )
        request.user = user
        response = views.structure_details(request, 1000000000001)
        # then
        self.assertEqual(response.status_code, 302)


class TestPocoDetailsModal(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        create_structures()
        cls.user, cls.owner = set_owner_character(character_id=1001)
        poco = cls.owner.structures.get(id=1200000000003)
        cls.details = PocoDetails.objects.create(
            structure=poco,
            alliance_tax_rate=0.02,
            allow_access_with_standings=True,
            allow_alliance_access=True,
            corporation_tax_rate=0.01,
            reinforce_exit_end=21,
            reinforce_exit_start=18,
        )
        cls.user = AuthUtils.add_permission_to_user_by_name(
            "structures.basic_access", cls.user
        )

    def test_should_load_correctly(self):
        # when
        request = self.factory.get(
            reverse("structures:poco_details", args=[1200000000003])
        )
        request.user = self.user
        response = views.poco_details(request, 1200000000003)
        # then
        self.assertEqual(response.status_code, 200)
