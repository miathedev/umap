import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from umap.models import Map

from ..base import DataLayerFactory

pytestmark = pytest.mark.django_db


def test_remote_layer_should_not_be_used_as_datalayer_for_created_features(
    map, live_server, datalayer, page
):
    # Faster than doing a login
    map.edit_status = Map.ANONYMOUS
    map.save()
    datalayer.settings["remoteData"] = {
        "url": "https://overpass-api.de/api/interpreter?data=[out:xml];node[harbour=yes]({south},{west},{north},{east});out body;",
        "format": "osm",
        "from": "10",
    }
    datalayer.save()
    page.goto(f"{live_server.url}{map.get_absolute_url()}?edit")
    toggle = page.get_by_title("See data layers")
    expect(toggle).to_be_visible()
    toggle.click()
    layers = page.locator(".umap-browse-datalayers li")
    expect(layers).to_have_count(1)
    map_el = page.locator("#map")
    add_marker = page.get_by_title("Draw a marker")
    expect(add_marker).to_be_visible()
    marker = page.locator(".leaflet-marker-icon")
    expect(marker).to_have_count(0)
    add_marker.click()
    map_el.click(position={"x": 100, "y": 100})
    expect(marker).to_have_count(1)
    # A new datalayer has been created to host this created feature
    # given the remote one cannot accept new features
    expect(layers).to_have_count(2)


def test_can_hide_datalayer_from_caption(map, live_server, datalayer, page):
    # Faster than doing a login
    map.edit_status = Map.ANONYMOUS
    map.save()
    # Add another DataLayer
    other = DataLayerFactory(map=map, name="Hidden", settings={"inCaption": False})
    page.goto(f"{live_server.url}{map.get_absolute_url()}")
    toggle = page.get_by_text("About").first
    expect(toggle).to_be_visible()
    toggle.click()
    layers = page.locator(".umap-caption .datalayer-legend")
    expect(layers).to_have_count(1)
    found = page.locator("#umap-ui-container").get_by_text(datalayer.name)
    expect(found).to_be_visible()
    hidden = page.locator("#umap-ui-container").get_by_text(other.name)
    expect(hidden).to_be_hidden()


def test_basic_choropleth_map(map, live_server, page):
    path = Path(__file__).parent.parent / "fixtures/choropleth_region_chomage.geojson"
    data = json.loads(path.read_text())
    DataLayerFactory(data=data, map=map)
    page.goto(f"{live_server.url}{map.get_absolute_url()}")
    # Hauts-de-France, PACA, Occitanie
    paths = page.locator("path[fill='#08306b']")
    expect(paths).to_have_count(3)
    # Normandie, Grand-Est, Centre-Val-de-Loire, IdF
    paths = page.locator("path[fill='#2171b5']")
    expect(paths).to_have_count(4)
    # Bourgogne-Franceh-Comté
    paths = page.locator("path[fill='#6baed6']")
    expect(paths).to_have_count(1)
    # Corse, Nouvelle-Aquitaine
    paths = page.locator("path[fill='#c6dbef']")
    expect(paths).to_have_count(2)
    # Bretagne, Pays de la Loire, AURA
    paths = page.locator("path[fill='#f7fbff']")
    expect(paths).to_have_count(3)
