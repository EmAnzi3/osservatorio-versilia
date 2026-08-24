#!/usr/bin/env python3
"""Verifica pan a un dito e pinch zoom Leaflet su viewport touch."""
from __future__ import annotations


def verify_touch_gestures(page, label: str) -> None:
    page.locator('.mapWrap').scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    box = page.locator('#map').bounding_box()
    if not box:
        raise AssertionError(f'Mappa non misurabile per gesti touch in {label}')
    x = box['x'] + box['width'] * .5
    y = box['y'] + box['height'] * .5
    session = page.context.new_cdp_session(page)
    before = page.evaluate("() => { const m=window.__ovPercorsiMap; const c=m.getCenter(); return {lat:c.lat,lng:c.lng,zoom:m.getZoom()}; }")
    session.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y,'radiusX':2,'radiusY':2,'force':1,'id':1}]})
    for dx, dy in ((20, 8), (45, 18), (70, 28)):
        session.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':x+dx,'y':y+dy,'radiusX':2,'radiusY':2,'force':1,'id':1}]})
        page.wait_for_timeout(35)
    session.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    page.wait_for_timeout(250)
    after_pan = page.evaluate("() => { const m=window.__ovPercorsiMap; const c=m.getCenter(); return {lat:c.lat,lng:c.lng,zoom:m.getZoom()}; }")
    moved = abs(after_pan['lat']-before['lat']) + abs(after_pan['lng']-before['lng'])
    if moved < 1e-5:
        raise AssertionError(f'Pan touch non modifica il centro mappa in {label}: {before} -> {after_pan}')

    z0 = after_pan['zoom']
    session.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[
        {'x':x-35,'y':y,'radiusX':2,'radiusY':2,'force':1,'id':1},
        {'x':x+35,'y':y,'radiusX':2,'radiusY':2,'force':1,'id':2}]})
    for spread in (55, 75, 100):
        session.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[
            {'x':x-spread,'y':y,'radiusX':2,'radiusY':2,'force':1,'id':1},
            {'x':x+spread,'y':y,'radiusX':2,'radiusY':2,'force':1,'id':2}]})
        page.wait_for_timeout(45)
    session.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    page.wait_for_timeout(300)
    z1 = page.evaluate("window.__ovPercorsiMap.getZoom()")
    if abs(float(z1)-float(z0)) < .1:
        raise AssertionError(f'Pinch touch non modifica lo zoom in {label}: {z0} -> {z1}')
