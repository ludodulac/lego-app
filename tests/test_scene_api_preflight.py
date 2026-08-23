from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _scene():
    return {
        "schema_version":"0.2","id":"preflight","name":"Preflight","units":"m",
        "volumes":[{
            "id":"main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":8,"source":{"kind":"inferred","confidence":.7}},
            "height":{"value":6,"source":{"kind":"inferred","confidence":.7}},
            "floors":2,"source":{"kind":"inferred","confidence":.7},
        }],
        "platforms":[{
            # This deliberately crosses the main left/rear corner. Scene contract
            # can describe the rectangle, but the current rectilinear exterior
            # builder requires it to be split before construction.
            "id":"corner_deck","position":{"x":-1,"y":7.5,"z":2},
            "width":1,"depth":1,"thickness":.2,"material":"timber",
            "source":{"kind":"inferred","confidence":.7},
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    }


def test_validate_scene_reports_exterior_builder_blocker_before_build():
    response=client.post("/api/v1/validate-scene",json=_scene())
    assert response.status_code==200
    payload=response.json()
    issues=payload["projection"]["issues"]
    blocker=next(issue for issue in issues if issue["code"]=="scene_architecture_not_buildable")
    assert blocker["severity"]=="blocker"
    assert "split" in blocker["message"].lower()


def test_build_scene_reuses_same_preflight_blocker():
    response=client.post("/api/v1/build-scene",json={"scene":_scene(),"front_width_studs":48})
    assert response.status_code==422
    assert "split" in response.json()["detail"].lower()
