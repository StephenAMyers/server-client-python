import requests
import urllib3

from defusedxml.ElementTree import fromstring
from packaging.version import Version
from .endpoint import (
    Sites,
    Views,
    Users,
    Groups,
    Workbooks,
    Datasources,
    Projects,
    Auth,
    Schedules,
    ServerInfo,
    Tasks,
    Subscriptions,
    Jobs,
    Metadata,
    Databases,
    Tables,
    Flows,
    Webhooks,
    DataAccelerationReport,
    Favorites,
    DataAlerts,
    Fileuploads,
    FlowRuns,
    Metrics,
)
from .endpoint.exceptions import (
    ServerInfoEndpointNotFoundError,
    EndpointUnavailableError,
)
from .exceptions import NotSignedInError
from ..namespace import Namespace


_PRODUCT_TO_REST_VERSION = {
    "10.0": "2.3",
    "9.3": "2.2",
    "9.2": "2.1",
    "9.1": "2.0",
    "9.0": "2.0",
}
minimum_supported_server_version = "2.3"
default_server_version = "2.3"


class Server(object):
    class PublishMode:
        Append = "Append"
        Overwrite = "Overwrite"
        CreateNew = "CreateNew"

    def __init__(self, server_address, use_server_version=False, http_options=None, session_factory=requests.Session):
        self._server_address = server_address
        self._auth_token = None
        self._site_id = None
        self._user_id = None
        self._session_factory = session_factory
        self._session = session_factory()
        self._http_options = dict()

        self.version = default_server_version
        self.auth = Auth(self)
        self.views = Views(self)
        self.users = Users(self)
        self.sites = Sites(self)
        self.groups = Groups(self)
        self.jobs = Jobs(self)
        self.workbooks = Workbooks(self)
        self.datasources = Datasources(self)
        self.favorites = Favorites(self)
        self.flows = Flows(self)
        self.projects = Projects(self)
        self.schedules = Schedules(self)
        self.server_info = ServerInfo(self)
        self.tasks = Tasks(self)
        self.subscriptions = Subscriptions(self)
        self.metadata = Metadata(self)
        self.databases = Databases(self)
        self.tables = Tables(self)
        self.webhooks = Webhooks(self)
        self.data_acceleration_report = DataAccelerationReport(self)
        self.data_alerts = DataAlerts(self)
        self.fileuploads = Fileuploads(self)
        self._namespace = Namespace()
        self.flow_runs = FlowRuns(self)
        self.metrics = Metrics(self)

        # must set this before calling use_server_version, because that's a server call
        if http_options:
            self.add_http_options(http_options)

        if use_server_version:
            self.use_server_version()

    def add_http_options(self, option_pair: dict):
        if not option_pair:
            # log debug message
            return
        if len(option_pair) != 1:
            raise ValueError(
                "Update headers one at a time. Expected type: ",
                {"key": 12}.__class__,
                "Actual type: ",
                option_pair,
                option_pair.__class__,
            )
        self._http_options.update(option_pair)
        if "verify" in option_pair.keys() and self._http_options.get("verify") is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # would be nice if you could turn them back on

    def clear_http_options(self):
        self._http_options = dict()

    def _clear_auth(self):
        self._site_id = None
        self._user_id = None
        self._auth_token = None
        self._session = self._session_factory()

    def _set_auth(self, site_id, user_id, auth_token):
        self._site_id = site_id
        self._user_id = user_id
        self._auth_token = auth_token

    def _get_legacy_version(self):
        response = self._session.get(self.server_address + "/auth?format=xml")
        info_xml = fromstring(response.content)
        prod_version = info_xml.find(".//product_version").text
        version = _PRODUCT_TO_REST_VERSION.get(prod_version, "2.1")  # 2.1
        return version

    def _determine_highest_version(self):
        try:
            old_version = self.version
            self.version = "2.4"
            version = self.server_info.get().rest_api_version
        except ServerInfoEndpointNotFoundError:
            version = self._get_legacy_version()

        finally:
            self.version = old_version

        return version

    def use_server_version(self):
        self.version = self._determine_highest_version()

    def use_highest_version(self):
        self.use_server_version()
        import warnings

        warnings.warn("use use_server_version instead", DeprecationWarning)

    def check_at_least_version(self, target: str):
        server_version = Version(self.version or "0.0")
        target_version = Version(target)
        return server_version >= target_version

    def assert_at_least_version(self, comparison: str, reason: str):
        if not self.check_at_least_version(comparison):
            error = "{} is not available in API version {}. Requires {}".format(reason, self.version, comparison)
            raise EndpointUnavailableError(error)

    @property
    def baseurl(self):
        return "{0}/api/{1}".format(self._server_address, str(self.version))

    @property
    def namespace(self):
        return self._namespace()

    @property
    def auth_token(self):
        if self._auth_token is None:
            error = "Missing authentication token. You must sign in first."
            raise NotSignedInError(error)
        return self._auth_token

    @property
    def site_id(self):
        if self._site_id is None:
            error = "Missing site ID. You must sign in first."
            raise NotSignedInError(error)
        return self._site_id

    @property
    def user_id(self):
        if self._user_id is None:
            error = "Missing user ID. You must sign in first."
            raise NotSignedInError(error)
        return self._user_id

    @property
    def server_address(self):
        return self._server_address

    @property
    def http_options(self):
        return self._http_options

    @property
    def session(self):
        return self._session

    def is_signed_in(self):
        return self._auth_token is not None
