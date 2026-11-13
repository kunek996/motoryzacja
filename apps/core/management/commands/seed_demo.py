"""Fill a LOCAL development database with fictional demo data.

    python manage.py seed_demo           # add demo data (idempotent)
    python manage.py seed_demo --reset   # wipe catalogue + demo users first

Demo accounts (development only, all use DEMO_PASSWORD below):
    admin@tunehub.test   – superuser / moderator (Django admin)
    demo@tunehub.test    – subscriber with active (simulated) subscription
    free@tunehub.test    – registered user without subscription (sees the paywall)
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import User
from apps.billing.models import Subscription
from apps.catalog.models import CarModel, Comment, Entry, EntryParameter, Make, Vote

DEMO_PASSWORD = "TuneHub-demo-2026"
DEMO_DOMAIN = "tunehub.test"

CARS = {
    "Audi": [("A3", "8V", 2012, 2020), ("S3", "8V", 2013, 2020), ("RS3", "8V", 2015, 2020), ("A4", "B8", 2007, 2015)],
    "BMW": [("3 Series", "E90", 2005, 2012), ("3 Series", "F30", 2011, 2019), ("M3", "E46", 2000, 2006), ("M140i", "F20", 2016, 2019)],
    "Volkswagen": [("Golf GTI", "MK7", 2013, 2020), ("Golf R", "MK7", 2014, 2020), ("Passat", "B8", 2014, None)],
    "Skoda": [("Octavia RS", "III", 2013, 2020), ("Superb", "III", 2015, None)],
    "Ford": [("Focus ST", "MK3", 2012, 2018), ("Focus RS", "MK3", 2015, 2018), ("Mustang", "S550", 2015, 2023)],
    "Mercedes-Benz": [("C-Class", "W205", 2014, 2021), ("A45 AMG", "W176", 2013, 2018)],
    "Toyota": [("GR Yaris", "", 2020, None), ("GR Supra", "A90", 2019, None)],
    "Subaru": [("WRX STI", "VA", 2014, 2021)],
    "Honda": [("Civic Type R", "FK8", 2017, 2021)],
    "Hyundai": [("i30 N", "PDe", 2017, None)],
    "Mazda": [("MX-5", "ND", 2015, None)],
    "Mitsubishi": [("Lancer Evolution", "X", 2007, 2016)],
}

AUTHORS = [
    ("kuba_turbo", "pl", "Hamownia w garażu, 15 lat z VAG."),
    ("mapmaster", "pl", "Kalibracje ECU, głównie Bosch MED/MG1."),
    ("dsg_doktor", "pl", "Skrzynie DSG i ZF – adaptacje, mapy TCU."),
    ("boostlab", "en", "Turbo upgrades and boost control nerd."),
    ("evo_hans", "de", "Mitsubishi & Subaru, Rallye-Technik."),
    ("track_daisy", "en", "Track days, reliability first."),
]

COMMENTS = [
    "Dzięki, działa u mnie bez problemu – logi wyglądają czysto.",
    "Jakie paliwo? Na 95 też trzymało te wartości?",
    "Great write-up. Did you have to upgrade the intercooler?",
    "Danke! Wie sieht es mit den Abgastemperaturen aus?",
    "Potwierdzam, na hamowni wyszło bardzo podobnie.",
    "Would love to see the logs at 6000 rpm.",
    "Sprzęgło stockowe wytrzymało? Mam 120 tys. km przebiegu.",
    "Top Anleitung, genau das habe ich gesucht.",
]

# (make, model, generation, category, lang, title, data, params, body)
ENTRIES = [
    ("Volkswagen", "Golf GTI", "MK7", "ecu", "pl", "Stage 1 dla 2.0 TSI EA888 Gen3 – 300 KM na pompie 98",
     dict(model_year=2016, fuel="petrol", engine="2.0 TSI EA888 Gen3 (CHHA)", ecu_type="Bosch MED17.5.25", gearbox="DQ250 DSG",
          stage="1", turbo="IS20 (stock)", boost_bar="1.45", power_before_hp=230, power_after_hp=300, torque_before_nm=350, torque_after_nm=420),
     [("Boost target @ 3000 rpm", "1.45", "bar"), ("Boost target @ 6000 rpm", "1.10", "bar"), ("Ignition advance max", "+2.0", "°"), ("Lambda pod pełnym obciążeniem", "0.82", "λ")],
     "Mapa testowana na 98 oktanach, intake stock, downpipe stock.\n\nNajważniejsze zmiany: podniesiony limit momentu w TCU (patrz osobny wpis o DQ250), "
     "łagodniejsze narastanie doładowania do 2500 rpm, żeby oszczędzać sprzęgła. Na 95 oktanach ECU zdejmuje ~1° wyprzedzenia, moc spada do ok. 290 KM.\n\n"
     "Logi: brak knock retard powyżej 1.5° na żadnym cylindrze. Temperatura dolotu do 45°C latem."),
    ("Volkswagen", "Golf GTI", "MK7", "tcu", "pl", "DQ250 – limit momentu i szybsze zmiany biegów (TCU)",
     dict(model_year=2016, fuel="petrol", engine="2.0 TSI EA888 Gen3", ecu_type="", gearbox="DQ250 (02E)", stage="1"),
     [("Torque limit", "450", "Nm"), ("Clamping pressure +", "8", "%"), ("Shift time (sport)", "≈ 120", "ms"), ("Launch control rpm", "3200", "rpm")],
     "Mapa TCU dopasowana do Stage 1 z wpisu obok. Podniesiony docisk sprzęgieł, skrócone czasy zmian w trybie S, wyłączone wczesne zmiany w D przy niskim obciążeniu.\n\n"
     "Po wgraniu koniecznie adaptacja sprzęgieł (podstawowe ustawienia w VCDS) i jazda testowa wg procedury."),
    ("Volkswagen", "Golf R", "MK7", "turbo", "en", "IS38 hybrid on Golf R – boost curve that keeps the turbo happy",
     dict(model_year=2018, fuel="petrol", engine="2.0 TSI EA888 Gen3 (CJXC)", ecu_type="Simos 18.1", gearbox="DQ381 DSG", stage="2",
          turbo="IS38 hybrid", boost_bar="1.80", power_before_hp=310, power_after_hp=420, torque_before_nm=400, torque_after_nm=520),
     [("Peak boost", "1.80", "bar"), ("Boost @ 6500 rpm", "1.35", "bar"), ("Wastegate duty max", "92", "%"), ("Turbo shaft speed limit", "190000", "rpm")],
     "The IS38 hybrid runs out of breath above 6000 rpm, so taper boost instead of chasing a flat line. Keep compressor speed under ~190k rpm.\n\n"
     "Supporting mods: upgraded intercooler, high-flow downpipe with cat, uprated HPFP internals. Fuel: 98 RON. EGT stayed under 920°C in 3rd gear pulls."),
    ("Audi", "S3", "8V", "ecu", "de", "S3 8V Stage 1 – sanfte Kennlinie für Alltag und Langlebigkeit",
     dict(model_year=2017, fuel="petrol", engine="2.0 TFSI EA888 Gen3", ecu_type="Bosch MED17.1.1", gearbox="S tronic DQ250", stage="1",
          turbo="IS38 (Serie)", boost_bar="1.55", power_before_hp=310, power_after_hp=365, torque_before_nm=380, torque_after_nm=460),
     [("Ladedruck max", "1.55", "bar"), ("Drehmomentbegrenzung", "460", "Nm"), ("Zündwinkel Vollast", "+1.5", "°")],
     "Bewusst konservativ abgestimmt: Drehmoment wird erst ab 2.800 U/min freigegeben, um das DQ250 zu schonen. Auf 98 ROZ getestet.\n\n"
     "Wichtig: Zündkerzen eine Stufe kälter (NGK PFR7S8EG) und Ölwechsel alle 10.000 km."),
    ("Audi", "RS3", "8V", "mod", "en", "RS3 8V: intake + intercooler + downpipe – measured gains",
     dict(model_year=2019, fuel="petrol", engine="2.5 TFSI DAZA", ecu_type="Simos 18.1", gearbox="DQ500", stage="2",
          turbo="Stock K16", boost_bar="1.70", power_before_hp=400, power_after_hp=470, torque_before_nm=480, torque_after_nm=600),
     [("IAT drop after IC (3rd gear pull)", "-18", "°C"), ("Peak boost", "1.70", "bar")],
     "Order of mods and dyno results on the same day, same dyno:\n1. Intake – +6 hp (mostly sound)\n2. Intercooler – +0 hp peak, but no heat soak on repeated pulls\n3. Downpipe with 200-cell cat + Stage 2 map – +64 hp\n\n"
     "Keep the catalyst: the car stays road legal and the gain difference vs catless was within dyno variance."),
    ("BMW", "3 Series", "F30", "ecu", "pl", "335i N55 – Stage 1 na pompie, wartości z logów",
     dict(model_year=2014, fuel="petrol", engine="N55B30", ecu_type="Bosch MEVD17.2", gearbox="ZF 8HP45", stage="1",
          turbo="Twin-scroll (stock)", boost_bar="1.15", power_before_hp=306, power_after_hp=360, torque_before_nm=400, torque_after_nm=500),
     [("Boost target", "1.15", "bar"), ("Torque limit (ZF)", "500", "Nm"), ("Timing max", "+1.5", "°")],
     "N55 dobrze reaguje na lekkie podniesienie doładowania. 8HP45 wymaga podniesienia limitu momentu w TCU, inaczej będzie ścinać moment na 1–2 biegu.\n\n"
     "Uwaga na wtryskiwacze – przy E-mixie trzeba już innego software."),
    ("BMW", "3 Series", "F30", "tcu", "en", "ZF 8HP45 xHP-style shift map for the F30 335i",
     dict(model_year=2014, fuel="petrol", engine="N55B30", gearbox="ZF 8HP45", stage="1"),
     [("Upshift rpm (Sport, full throttle)", "6800", "rpm"), ("Torque limit", "550", "Nm"), ("Downshift blip", "on", "")],
     "Faster, firmer shifts in Sport and no early upshifts in Comfort. Torque limit raised to 550 Nm to match tuned engines. Re-run gearbox adaptations afterwards."),
    ("BMW", "M3", "E46", "mod", "de", "S54: Einzeldrosseln richtig synchronisieren",
     dict(model_year=2003, fuel="petrol", engine="S54B32", ecu_type="Siemens MSS54HP", gearbox="Getrag 420G", stage="0",
          power_before_hp=343, power_after_hp=343),
     [("Drosselklappen-Synchronisation", "± 0.1", "kPa"), ("Ventilspiel Einlass", "0.18–0.23", "mm")],
     "Kein Leistungs-Tuning, sondern Wartung: Nach der Synchronisation der Drosselklappen lief der Leerlauf deutlich ruhiger und der Motor hängt besser am Gas. Schritt-für-Schritt-Anleitung mit Unterdruckmessgerät."),
    ("Skoda", "Octavia RS", "III", "ecu", "pl", "Octavia RS 2.0 TDI 184 KM – Stage 1 z zachowaniem DPF i EGR",
     dict(model_year=2017, fuel="diesel", engine="2.0 TDI EA288 (CUNA)", ecu_type="Bosch EDC17C64", gearbox="DQ250 DSG", stage="1",
          turbo="VGT (stock)", boost_bar="1.50", power_before_hp=184, power_after_hp=220, torque_before_nm=380, torque_after_nm=440),
     [("Doładowanie max", "1.50", "bar"), ("Czas wtrysku max", "+6", "%"), ("Limit dymienia (lambda min)", "1.15", "λ")],
     "Mapa w pełni zgodna z homologacją emisyjną: DPF, EGR i SCR działają normalnie, regeneracje bez zmian. Limit dymienia pozostawiony fabryczny, więc brak czarnego dymu przy ostrym gazie.\n\n"
     "Spalanie w trasie bez zmian (~5.5 l/100 km)."),
    ("Skoda", "Superb", "III", "mod", "pl", "Superb 2.0 TSI 280 – chłodzenie DSG przy holowaniu przyczepy",
     dict(model_year=2018, fuel="petrol", engine="2.0 TSI EA888 Gen3 (CJXA)", gearbox="DQ500 DSG", stage="0"),
     [("Temp. oleju DSG przed", "128", "°C"), ("Temp. oleju DSG po", "104", "°C")],
     "Dodatkowa chłodnica oleju skrzyni z zestawu od Superba 4x4 + termostat 90°C. Przy przyczepie 1600 kg na podjazdach skrzynia przestała przechodzić w tryb awaryjny."),
    ("Ford", "Focus ST", "MK3", "ecu", "en", "Focus ST 2.0 EcoBoost – Stage 1 that stays knock-free on 95 RON",
     dict(model_year=2016, fuel="petrol", engine="2.0 EcoBoost", ecu_type="Bosch MED17.0", gearbox="MT66 manual", stage="1",
          turbo="BorgWarner K03 (stock)", boost_bar="1.35", power_before_hp=250, power_after_hp=285, torque_before_nm=360, torque_after_nm=420),
     [("Peak boost", "1.35", "bar"), ("Spark advance cap", "-1.0", "°"), ("Torque request limit 1st gear", "330", "Nm")],
     "Map designed for 95 RON (European premium fuel is not always available). 1st gear torque is limited to reduce torque steer and save the clutch."),
    ("Ford", "Focus RS", "MK3", "mod", "en", "Head gasket fix for 2.3 EcoBoost (Focus RS) – what we did",
     dict(model_year=2016, fuel="petrol", engine="2.3 EcoBoost", gearbox="MT82", stage="0"),
     [("Coolant loss before fix", "≈ 200", "ml/1000 km"), ("Coolant loss after", "0", "ml/1000 km")],
     "Revised head gasket kit and new head bolts, coolant system pressure test before and after. Includes torque sequence and tips for checking the block deck flatness."),
    ("Ford", "Mustang", "S550", "tcu", "de", "Mustang 10R80: Schaltpunkte für Rennstrecke",
     dict(model_year=2019, fuel="petrol", engine="5.0 Coyote Gen3", gearbox="10R80", stage="c"),
     [("Hochschaltdrehzahl (Track)", "7300", "U/min"), ("Wandlerüberbrückung ab", "3. Gang", "")],
     "Angepasste Schaltpunkte für den Track-Modus, frühere Wandlerüberbrückung und kein Überspringen von Gängen beim Hochschalten. Getriebeöltemperatur beobachten!"),
    ("Mercedes-Benz", "A45 AMG", "W176", "turbo", "en", "M133 twin-scroll turbo: boost control after wastegate actuator swap",
     dict(model_year=2016, fuel="petrol", engine="M133 2.0 turbo", ecu_type="Bosch MED17.7.3", gearbox="AMG Speedshift DCT", stage="2",
          turbo="BorgWarner twin-scroll (stock)", boost_bar="1.95", power_before_hp=381, power_after_hp=430, torque_before_nm=475, torque_after_nm=530),
     [("Wastegate preload", "+2", "mm"), ("Peak boost", "1.95", "bar"), ("Boost overshoot max", "0.08", "bar")],
     "After replacing the wastegate actuator, the PID boost control oscillated. Reducing the I-term by 15% removed the overshoot. Logs attached in the full entry."),
    ("Mercedes-Benz", "C-Class", "W205", "ecu", "pl", "C220d OM651 – Stage 1 eco (spalanie i moment w trasie)",
     dict(model_year=2015, fuel="diesel", engine="OM651 2.1 CDI", ecu_type="Delphi CRD3", gearbox="7G-Tronic", stage="1",
          boost_bar="1.60", power_before_hp=170, power_after_hp=205, torque_before_nm=400, torque_after_nm=460),
     [("Doładowanie max", "1.60", "bar"), ("Limit momentu 7G", "460", "Nm")],
     "Mapa ukierunkowana na elastyczność 1500–2500 rpm. Układy oczyszczania spalin bez zmian. Spadek spalania w trasie o ok. 0.3 l/100 km."),
    ("Toyota", "GR Yaris", "", "ecu", "en", "GR Yaris G16E-GTS – mild map + intercooler sprayer logic",
     dict(model_year=2021, fuel="petrol", engine="G16E-GTS 1.6 turbo", ecu_type="Denso", gearbox="6MT", stage="1",
          turbo="Single-scroll (stock)", boost_bar="1.85", power_before_hp=261, power_after_hp=300, torque_before_nm=360, torque_after_nm=420),
     [("Peak boost", "1.85", "bar"), ("IC sprayer trigger (IAT)", "40", "°C")],
     "Map keeps the stock rev limiter and only raises boost in the midrange. IC sprayer enabled automatically above 40°C intake air temperature."),
    ("Toyota", "GR Supra", "A90", "ecu", "de", "Supra B58 – Stufe 1 mit 98 ROZ",
     dict(model_year=2020, fuel="petrol", engine="B58B30", ecu_type="Bosch MG1CS003", gearbox="ZF 8HP51", stage="1",
          turbo="Twin-scroll (Serie)", boost_bar="1.30", power_before_hp=340, power_after_hp=420, torque_before_nm=500, torque_after_nm=600),
     [("Ladedruck max", "1.30", "bar"), ("Drehmomentlimit 8HP", "650", "Nm")],
     "Der B58 hat viel Reserve. Mit 98 ROZ und Serien-Hardware stabile 420 PS. Getriebesteuerung wurde mitangepasst (Drehmomentlimit)."),
    ("Subaru", "WRX STI", "VA", "turbo", "de", "EJ257: Ladedruckregelung mit 3-Port-Ventil",
     dict(model_year=2018, fuel="petrol", engine="EJ257", ecu_type="Denso SH72543", gearbox="6MT", stage="2",
          turbo="VF48", boost_bar="1.40", power_before_hp=300, power_after_hp=355, torque_before_nm=407, torque_after_nm=460),
     [("Wastegate-Duty Basis", "48", "%"), ("Ladedruck max", "1.40", "bar"), ("Drehzahl Spool", "3200", "U/min")],
     "3-Port-Magnetventil ersetzt das Serienventil. Basis-Duty neu kalibriert, Ladedruckspitzen damit von 0,2 auf 0,05 bar reduziert. Kolben-Ringstege beim EJ beachten!"),
    ("Mitsubishi", "Lancer Evolution", "X", "ecu", "de", "Evo X 4B11T – E85 Flex-Fuel Abstimmung",
     dict(model_year=2010, fuel="e85", engine="4B11T", ecu_type="Mitsubishi (Renesas SH7058)", gearbox="5MT", stage="2",
          turbo="Serie (TD05)", boost_bar="1.75", power_before_hp=295, power_after_hp=380, torque_before_nm=407, torque_after_nm=480),
     [("Ethanolanteil", "70–85", "%"), ("Einspritzdüsen", "1050", "cc"), ("Ladedruck max", "1.75", "bar")],
     "Mit Ethanolsensor wird zwischen Benzin- und E85-Kennfeld interpoliert. Größere Einspritzdüsen und Kraftstoffpumpe sind Pflicht."),
    ("Honda", "Civic Type R", "FK8", "mod", "en", "FK8 Type R: brake cooling and pad choice for track days",
     dict(model_year=2019, fuel="petrol", engine="K20C1", gearbox="6MT", stage="0"),
     [("Front rotor temp after 5 laps (before)", "780", "°C"), ("After brake ducts", "640", "°C")],
     "Brake ducts from the front bumper + higher-temperature pads + DOT 5.1 fluid. Fade gone after 20-minute sessions. Street noise slightly higher."),
    ("Hyundai", "i30 N", "PDe", "ecu", "pl", "i30 N Performance – Stage 1 + logi z toru",
     dict(model_year=2019, fuel="petrol", engine="2.0 T-GDi Theta II", ecu_type="Bosch MG1CS", gearbox="6MT", stage="1",
          boost_bar="1.50", power_before_hp=275, power_after_hp=310, torque_before_nm=378, torque_after_nm=430),
     [("Doładowanie max", "1.50", "bar"), ("Temp. dolotu na torze", "52", "°C")],
     "Mapa testowana na Torze Poznań – 4 sesje po 20 min bez zmniejszania mocy przez ECU. Zalecany mocniejszy intercooler przy cieplejszej pogodzie."),
    ("Mazda", "MX-5", "ND", "mod", "en", "MX-5 ND: geometry settings for fast road + track",
     dict(model_year=2017, fuel="petrol", engine="SKYACTIV-G 2.0", gearbox="6MT", stage="0"),
     [("Camber front", "-1.5", "°"), ("Camber rear", "-2.0", "°"), ("Toe rear (total)", "0.25", "°")],
     "No engine changes: just alignment. The car turns in much better and is still friendly on wet roads. Tyre wear is even after 8000 km."),
    ("Audi", "A4", "B8", "ecu", "pl", "A4 B8 2.0 TDI CAGA – Stage 1, zachowany DPF",
     dict(model_year=2011, fuel="diesel", engine="2.0 TDI CR (CAGA)", ecu_type="Bosch EDC17CP14", gearbox="6MT", stage="1",
          boost_bar="1.40", power_before_hp=143, power_after_hp=175, torque_before_nm=320, torque_after_nm=380),
     [("Doładowanie max", "1.40", "bar"), ("Limit dymienia", "fabryczny", "")],
     "Bezpieczna mapa dla aut z dużym przebiegiem. DPF i EGR aktywne. Przy dwumasie po 250 tys. km zalecam ograniczyć moment do 360 Nm."),
    ("BMW", "M140i", "F20", "ecu", "en", "M140i B58 – stage 1 on stock hardware (pump fuel)",
     dict(model_year=2018, fuel="petrol", engine="B58B30", ecu_type="Bosch MEVD17.2.G", gearbox="ZF 8HP45", stage="1",
          boost_bar="1.25", power_before_hp=340, power_after_hp=400, torque_before_nm=500, torque_after_nm=560),
     [("Peak boost", "1.25", "bar"), ("Torque limit ZF", "600", "Nm")],
     "Very safe B58 map. Keep stock downpipe with cat. Do not forget the gearbox torque limit, otherwise you lose torque in 1st–3rd."),
]


class Command(BaseCommand):
    help = "Create fictional demo data for local development."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete catalogue data and demo users first")

    @transaction.atomic
    def handle(self, *args, reset=False, **opts):
        if not settings.DEBUG:
            raise CommandError("seed_demo is for local development only (DEBUG=True).")
        rnd = random.Random(42)

        if reset:
            Entry.objects.all().delete()
            CarModel.objects.all().delete()
            Make.objects.all().delete()
            User.objects.filter(email__endswith="@" + DEMO_DOMAIN).delete()

        users = self._users()
        models = self._cars()
        authors = [users[name] for name, *_ in AUTHORS]

        created = 0
        now = timezone.now()
        for i, (make, model, gen, cat, lang, title, data, params, body) in enumerate(ENTRIES):
            car = models[(make, model, gen)]
            if Entry.objects.filter(title=title).exists():
                continue
            data = dict(data)
            if data.get("boost_bar"):
                data["boost_bar"] = Decimal(data["boost_bar"])
            author = authors[i % len(authors)]
            entry = Entry.objects.create(
                author=author, car_model=car, category=cat, language=lang, title=title, body=body, **data
            )
            # Spread creation dates over the last ~3 months for a realistic feed.
            Entry.objects.filter(pk=entry.pk).update(created_at=now - timedelta(days=rnd.randint(0, 90), hours=rnd.randint(0, 23)))
            for pos, (name, value, unit) in enumerate(params):
                EntryParameter.objects.create(entry=entry, name=name, value=value, unit=unit, position=pos)
            voters = [u for u in users.values() if u != author and u.has_access]
            for voter in rnd.sample(voters, k=rnd.randint(0, len(voters))):
                Vote.objects.get_or_create(entry=entry, user=voter)
            for _ in range(rnd.randint(0, 3)):
                Comment.objects.create(entry=entry, author=rnd.choice(voters), body=rnd.choice(COMMENTS))
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Demo data ready: {created} new entries, {Entry.objects.count()} total."))
        self.stdout.write(f"Demo logins (password in {__name__.replace('.', '/')}.py → DEMO_PASSWORD):")
        for email in (f"admin@{DEMO_DOMAIN}", f"demo@{DEMO_DOMAIN}", f"free@{DEMO_DOMAIN}"):
            self.stdout.write(f"  {email}")

    def _user(self, email, name, *, lang="pl", bio="", paid=False, staff=False):
        user = User.objects.filter(email=email).first()
        if not user:
            factory = User.objects.create_superuser if staff else User.objects.create_user
            user = factory(email, DEMO_PASSWORD, display_name=name)
        now = timezone.now()
        User.objects.filter(pk=user.pk).update(
            email_verified=True, preferred_language=lang, bio=bio,
            terms_accepted_at=now, privacy_accepted_at=now,
        )
        if paid:
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "stripe_customer_id": f"dev_cus_{user.pk}", "stripe_subscription_id": f"dev_sub_{user.pk}",
                    "status": "active", "current_period_end": now + timedelta(days=30),
                },
            )
        return User.objects.get(pk=user.pk)

    def _users(self):
        users = {
            "admin": self._user(f"admin@{DEMO_DOMAIN}", "admin", staff=True, bio="Moderator"),
            "demo_tuner": self._user(f"demo@{DEMO_DOMAIN}", "demo_tuner", paid=True, bio="Konto demonstracyjne."),
            "free_rider": self._user(f"free@{DEMO_DOMAIN}", "free_rider"),
        }
        for name, lang, bio in AUTHORS:
            users[name] = self._user(f"{name}@{DEMO_DOMAIN}", name, lang=lang, bio=bio, paid=True)
        return users

    def _cars(self):
        result = {}
        for make_name, models in CARS.items():
            make, _ = Make.objects.get_or_create(name=make_name, defaults={"slug": slugify(make_name)})
            for name, gen, y1, y2 in models:
                car, _ = CarModel.objects.get_or_create(
                    make=make, name=name, generation=gen, defaults={"year_from": y1, "year_to": y2}
                )
                result[(make_name, name, gen)] = car
        return result
