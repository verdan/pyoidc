__author__ = 'rohe0002'

from oic import oic
from oic.utils import time_util
from oic import oauth2

def _eq(l1, l2):
    return set(l1) == set(l2)


class TestOICClient():
    def setup_class(self):
        self.client = oic.Client("1")
        self.client.redirect_uri = "http://example.com/redirect"

    def test_areq_1(self):
        ar = self.client.get_authorization_request(response_type=["code"])

        assert ar.redirect_uri == "http://example.com/redirect"
        assert ar.response_type == ["code"]
        assert ar.client_id == "1"
        assert ar.state is None
        assert ar.scope == []

    def test_areq_2(self):
        self.client.state = "xyz"
        ar = self.client.get_authorization_request(response_type=["code"],
                                                   scope=["foo", "bar"])

        assert ar.redirect_uri == "http://example.com/redirect"
        assert ar.response_type == ["code"]
        assert ar.client_id == "1"
        assert ar.state == "xyz"
        assert ar.scope == ["foo", "bar"]

    def test_areq_replace_default_state(self):
        self.client.state = "xyz"
        ar = self.client.get_authorization_request(response_type=["code"],
                                                   scope = ["foo", "bar"])

        assert ar.redirect_uri == "http://example.com/redirect"
        assert ar.response_type == ["code"]
        assert ar.client_id == "1"
        assert ar.state == "xyz"
        assert ar.scope == ["foo", "bar"]

    def test_parse_authz_resp_url(self):
        url = "https://client.example.com/cb?code=SplxlOBeZQQYbYS6WxSbIA&state=xyz"
        aresp = self.client.parse_authorization_response(url=url)

        assert aresp.code == "SplxlOBeZQQYbYS6WxSbIA"
        assert aresp.state == "xyz"

        assert self.client.grant[""]
        assert self.client.grant[""].code == aresp.code
        assert self.client.grant[""].grant_expiration_time

    def test_parse_authz_resp_query(self):
        query = "code=SplxlOBeZQQYbYS6WxSbIA&state=abc"
        aresp = self.client.parse_authorization_response(query=query,
                                                         scope="foo")

        assert aresp.code == "SplxlOBeZQQYbYS6WxSbIA"
        assert aresp.state == "abc"

        assert self.client.grant["foo"]
        assert self.client.grant["foo"].code == aresp.code
        assert self.client.grant["foo"].grant_expiration_time

    def test_parse_authz_resp_query_multi_scope(self):
        query = "code=SplxlOBeZQQYbYS6WxAAAA&state=def"
        aresp = self.client.parse_authorization_response(query=query,
                                                         scope="foo bar")

        assert aresp.code == "SplxlOBeZQQYbYS6WxAAAA"
        assert aresp.state == "def"

        assert self.client.grant["foo bar"]
        assert self.client.grant["foo bar"].code == aresp.code
        assert self.client.grant["foo bar"].grant_expiration_time

        assert _eq(self.client.grant.keys(), ['', 'foo bar', 'foo'])

    def test_parse_authz_resp_query_unknown_parameter(self):
        query = "code=SplxlOBeZQQYbYS6WxSbIA&state=rst&foo=bar"
        aresp = self.client.parse_authorization_response(query=query,
                                                         scope="bar")

        assert aresp.code == "SplxlOBeZQQYbYS6WxSbIA"
        assert aresp.state == "rst"

        print aresp.__dict__.keys()
        assert "foo" not in aresp.__dict__

        assert self.client.grant["bar"]
        assert self.client.grant["bar"].code == aresp.code
        assert self.client.grant["bar"].grant_expiration_time

    def test_get_access_token_request_1(self):
        self.client.reset()
        self.client.redirect_uri = "http://client.example.com/authz"
        grant = oauth2.Grant()
        grant.code = "AbCdEf"
        grant.grant_expiration_time = time_util.time_sans_frac() + 30
        self.client.grant = {"": grant}

        # scope is default=""
        atr = self.client.get_access_token_request()

        assert atr.grant_type == "authorization_code"
        assert atr.code == "AbCdEf"
        assert atr.redirect_uri == "http://client.example.com/authz"

    def test_get_access_token_request_override(self):
        self.client.reset()
        self.client.redirect_uri = "http://client.example.com/authz"
        grant = oauth2.Grant()
        grant.code = "AbCdEf"
        grant.grant_expiration_time = time_util.time_sans_frac() + 30
        self.client.grant = {"xyz": grant}

        atr = self.client.get_access_token_request(scope="xyz")

        assert atr.grant_type == "authorization_code"
        assert atr.code == "AbCdEf"
        assert atr.redirect_uri == "http://client.example.com/authz"

    def test_parse_access_token_response(self):
        jso = """{
       "access_token":"2YotnFZFEjr1zCsicMWpAA",
       "token_type":"example",
       "expires_in":3600,
       "refresh_token":"tGzv3JOkF0XG5Qx2TlKWIA",
       "example_parameter":"example_value"
     }"""

        self.client.parse_access_token_response(info="".join([
                                        x.strip() for x in jso.split("\n")]))

        assert self.client.grant
        _grant = self.client.grant[""]
        assert _grant.access_token == "2YotnFZFEjr1zCsicMWpAA"
        assert _grant.token_type == "example"
        assert _grant.expires_in == 3600
        assert _grant.refresh_token == "tGzv3JOkF0XG5Qx2TlKWIA"
        # I'm dropping parameters I don't recognize
        assert "example_parameter" not in self.client.__dict__

        assert self.client.access_token_is_valid()

    def test_get_access_token_refresh_1(self):
        # Uses refresh_token from previous response
        atr = self.client.get_access_token_refresh()

        assert isinstance(atr, oauth2.RefreshAccessTokenRequest)
        assert atr.grant_type == "refresh_token"
        assert atr.refresh_token == "tGzv3JOkF0XG5Qx2TlKWIA"


    def test_parse_authz_err_response(self):
        ruri = "https://client.example.com/cb?error=access_denied&amp;state=xyz"

        resp = self.client.parse_authorization_response(url=ruri)

        assert isinstance(resp, oauth2.AuthorizationErrorResponse)

        assert resp.error == "access_denied"
        assert resp.state == "xyz"


    def test_parse_authz_response_2(self):
        ruri = "nonce=rld7t7eXH7GR&code=enAPFuUhruD7AkUB0PKS%2F66XFJEtgOmWuKPpmTcG4ag%3D&state=2aa45025b0578eddcfcdf979b4f344b7&scope=openid"
        resp = self.client.parse_authorization_response(query=ruri)

        assert isinstance(resp, oic.AuthorizationResponse)

        assert resp.nonce == "rld7t7eXH7GR"
        assert resp.state == "2aa45025b0578eddcfcdf979b4f344b7"
        assert resp.scope == ["openid"]

    def test_get_authorization_request_with_request(self):
        self.client.key="a1b2c3d4"
        self.client.algorithm = "HS256"

        arr = self.client.get_authorization_request_with_request(
            response_type=["code"],
            scope=["openid"],
            state="xyz012"
        )

        print arr
        assert arr
        assert arr.request
