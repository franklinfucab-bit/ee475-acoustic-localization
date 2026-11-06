"""Receiver controls. This application never opens an audio output device."""

PROFILES={'20 kHz beacon | 19-21 kHz':'coded-20',
          'Gap test | 18-22 kHz':'coded-gap'}

class ScanControls:
    def __init__(self,session):
        self.session=session
        self.profile='coded-20'
        self.session.set_running(False)
        self.session.set_mode(self.profile)

    @property
    def running(self):
        return self.session.want_running.is_set()

    def toggle_scan(self):
        self.session.set_running(not self.running)

    def select_profile(self,profile):
        from beacon_dsp import PROFILES as RECEIVERS
        if profile not in RECEIVERS:
            raise ValueError('Unknown receiver profile')
        if profile==self.profile:
            return
        self.profile=profile
        self.session.set_mode(profile)

    def close(self):
        self.session.set_running(False)
        self.session.stop.set()

