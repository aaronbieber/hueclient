import requests
import time


class Hue:
    def __init__(self, ip, username):
        self.ip = ip
        self.username = username
        self.url_template = "http://%s/api/%s" % (self.ip, self.username)
        self.lights = {}

    def parse_hue_response(self, raw_response):
        if len(raw_response) > 0:
            try:
                if "success" in raw_response[0].keys():
                    return True
            except:
                return False

        return False

    def api_path(self, path):
        """Return the full URL to an API endpoint at PATH.

        Exclude the leading slash at the beginning of PATH, it will be
        added for you."""

        return "%s/%s" % (self.url_template, path)

    def get_configuration(self):
        url = self.api_path("config")
        r = requests.get(url)

        if r.status_code == 200:
            return r.json()

        return False

    def get_lights(self):
        if not len(self.lights):
            url = self.api_path("lights")
            r = requests.get(url)

            if r.status_code == 200:
                self.lights = r.json()
            else:
                return False

        return self.lights

    def get_light_state(self, light_ids):
        ret = {}
        for light_id in light_ids:
            url = self.api_path("lights/%s" % light_id)
            r = requests.get(url)
            ret[light_id] = r.json()

            if len(light_ids) > 1:
                time.sleep(0.05)

        return ret

    def set_light_power(self, light_ids, power):
        state = {"on": power}
        return self.set_light_state(light_ids, state)

    def set_light_brightness(self, light_ids, brightness):
        brightness = int(brightness)
        if brightness > 254:
            brightness = 254

        state = {"on": True, "bri": brightness}
        return self.set_light_state(light_ids, state)

    def set_light_state(self, light_ids, state):
        ret = {}
        for light_id in light_ids:
            url = self.api_path("lights/%s/state" % light_id)
            r = requests.put(url, json=state)
            ret[light_id] = self.parse_hue_response(r.json())

            if len(light_ids) > 1:
                time.sleep(0.05)

        return ret

    def set_light_color(self, light_id, color):
        pass
