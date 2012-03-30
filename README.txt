Livestreams and archived streams from gaming sites like own3d.tv (currently only), justin.tv/twitch.tv (planned)

Current features:
    Livestreams from own3d.tv for the most popular games.

Planned:
    - Archive videos from own3d.tv, just have to do some parsing on the xml returned from the api and add listings in
    XBMC.
    - Livestreams and archives from justin.tv/twitch.tv
    - Other potential major livestream sources.


Installation:
    - you probably need XBMC 'eden', crashed on 'dharma'
    - only tested on linux so far, on eden.
    - requirements.pip lists python modules required. I've bundled the libraries since lxml, and most probably
      beaker, does not have binary distributions in official XBMC repos. Tested on one other system, which worked, but
      YMMV. If it fails due to importing any of these modules, it's probably best to just compile them yourself and
      replace the ones I've bundled.
    - clone/unzip into your $XBMC_HOME/addons folder
    - start XBMC and navigate to Videos->Addons
    - Not working? Check the log ($XBMC_HOME/temp/xbmc.log) and let me know.
