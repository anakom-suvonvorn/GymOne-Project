## for better tracking n stuf

please put `########` (how ever many you want)

next to the part of the api that is done and is able to run

example
```
@router.get("/showclass") ########
def show_available_classes(gym = Depends(get_gym)):
    classes = gym.get_available_classes()
    return {
        "classes": classes,
    }
```

use .get for optional stuff
