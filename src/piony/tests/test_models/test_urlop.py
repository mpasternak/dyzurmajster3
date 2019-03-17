from piony.models import Urlop, ZyczeniaPracownika


def test_urlop_str(zp):
    u = Urlop.objects.create(parent=zp, start="2019-01-01", koniec="2019-01-02")

    assert str(u) is not None
