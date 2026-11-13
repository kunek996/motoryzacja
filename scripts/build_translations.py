"""Generate locale/<lang>/LC_MESSAGES/django.po and compile .mo (no GNU gettext needed).

Source language in code/templates is English. Add new strings to T below, then run:
    python scripts/build_translations.py
(Once GNU gettext is installed you can switch to `manage.py makemessages` / `compilemessages`.)
"""
from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parent.parent

# msgid: (pl, de)
T = {
    "Polski": ("Polski", "Polski"),
    "English": ("English", "English"),
    "Deutsch": ("Deutsch", "Deutsch"),
    "Library": ("Biblioteka", "Bibliothek"),
    "Add entry": ("Dodaj wpis", "Eintrag hinzufügen"),
    "Subscribe": ("Subskrybuj", "Abonnieren"),
    "Log out": ("Wyloguj", "Abmelden"),
    "Log in": ("Zaloguj", "Anmelden"),
    "Sign up": ("Załóż konto", "Registrieren"),
    "Language": ("Język", "Sprache"),
    "Terms of Service": ("Regulamin", "Nutzungsbedingungen"),
    "Privacy Policy": ("Polityka prywatności", "Datenschutzerklärung"),
    "The community for car tuners": ("Społeczność pasjonatów tuningu", "Die Community für Fahrzeug-Tuner"),
    "Share and find modifications, engine and gearbox maps, and turbo settings for every make.":
        ("Wymieniaj się i znajduj modyfikacje, mapy silników i skrzyń biegów oraz ustawienia turbo dla każdej marki.",
         "Teile und finde Modifikationen, Motor- und Getriebekennfelder sowie Turbo-Einstellungen für jede Marke."),
    "Get access: $5 / month": ("Uzyskaj dostęp: 5 $ / miesiąc", "Zugang erhalten: 5 $ / Monat"),
    "Latest entries": ("Najnowsze wpisy", "Neueste Einträge"),
    "No entries yet.": ("Brak wpisów.", "Noch keine Einträge."),
    "No entries found.": ("Nie znaleziono wpisów.", "Keine Einträge gefunden."),
    "Create account": ("Utwórz konto", "Konto erstellen"),
    "Check your inbox": ("Sprawdź skrzynkę", "Posteingang prüfen"),
    "We sent you a link to confirm your email address. It is valid for 48 hours.":
        ("Wysłaliśmy link potwierdzający adres e-mail. Jest ważny 48 godzin.",
         "Wir haben dir einen Bestätigungslink gesendet. Er ist 48 Stunden gültig."),
    "Forgot your password?": ("Nie pamiętasz hasła?", "Passwort vergessen?"),
    "My account": ("Moje konto", "Mein Konto"),
    "Change password": ("Zmień hasło", "Passwort ändern"),
    "Reset password": ("Resetuj hasło", "Passwort zurücksetzen"),
    "Set new password": ("Ustaw nowe hasło", "Neues Passwort festlegen"),
    "Send reset link": ("Wyślij link", "Link senden"),
    "Subscription": ("Subskrypcja", "Abonnement"),
    "Active.": ("Aktywna.", "Aktiv."),
    "No active subscription.": ("Brak aktywnej subskrypcji.", "Kein aktives Abonnement."),
    "Manage subscription": ("Zarządzaj subskrypcją", "Abonnement verwalten"),
    "Your data (GDPR)": ("Twoje dane (RODO)", "Deine Daten (DSGVO)"),
    "Download all my data (JSON)": ("Pobierz wszystkie moje dane (JSON)", "Alle meine Daten herunterladen (JSON)"),
    "Delete my account": ("Usuń moje konto", "Mein Konto löschen"),
    "This cancels your subscription and permanently erases your account. Your published entries stay available but are no longer linked to you. This cannot be undone.":
        ("To anuluje subskrypcję i trwale usuwa konto. Twoje wpisy pozostaną widoczne, ale nie będą już z Tobą powiązane. Tej operacji nie można cofnąć.",
         "Dies kündigt dein Abonnement und löscht dein Konto dauerhaft. Deine Einträge bleiben erhalten, sind aber nicht mehr mit dir verknüpft. Dies kann nicht rückgängig gemacht werden."),
    "Delete permanently": ("Usuń trwale", "Endgültig löschen"),
    "If an account with that email exists, we sent password reset instructions.":
        ("Jeśli konto z tym adresem istnieje, wysłaliśmy instrukcję resetu hasła.",
         "Falls ein Konto mit dieser E-Mail existiert, haben wir Anweisungen zum Zurücksetzen gesendet."),
    "Full access": ("Pełny dostęp", "Voller Zugang"),
    "month": ("miesiąc", "Monat"),
    "Maps, settings and modifications for every make": ("Mapy, ustawienia i modyfikacje dla każdej marki", "Kennfelder, Einstellungen und Modifikationen für jede Marke"),
    "Download attachments and add your own entries": ("Pobieraj załączniki i dodawaj własne wpisy", "Anhänge herunterladen und eigene Einträge erstellen"),
    "Cancel any time": ("Anuluj w dowolnym momencie", "Jederzeit kündbar"),
    "Secure payment by Stripe. Taxes are added at checkout where applicable.":
        ("Bezpieczna płatność przez Stripe. Podatki dolicza się w kasie, jeśli dotyczy.",
         "Sichere Zahlung über Stripe. Steuern werden ggf. beim Bezahlen hinzugefügt."),
    "Sign up to subscribe": ("Załóż konto, aby subskrybować", "Registrieren, um zu abonnieren"),
    "Thank you!": ("Dziękujemy!", "Vielen Dank!"),
    "Your payment is being confirmed. Access is activated within a few seconds; refresh this page if needed.":
        ("Płatność jest potwierdzana. Dostęp aktywuje się w kilka sekund; w razie potrzeby odśwież stronę.",
         "Deine Zahlung wird bestätigt. Der Zugang wird in wenigen Sekunden aktiviert; lade die Seite ggf. neu."),
    "Go to the library": ("Przejdź do biblioteki", "Zur Bibliothek"),
    "Status": ("Status", "Status"),
    "renews/ends": ("odnawia się/kończy", "verlängert/endet"),
    "Cancellation scheduled at period end.": ("Anulowanie zaplanowane na koniec okresu.", "Kündigung zum Periodenende vorgemerkt."),
    "Billing portal (card, invoices, cancel)": ("Portal płatności (karta, faktury, anulowanie)", "Abrechnungsportal (Karte, Rechnungen, Kündigung)"),
    "No subscription.": ("Brak subskrypcji.", "Kein Abonnement."),
    "Search": ("Szukaj", "Suchen"),
    "All categories": ("Wszystkie kategorie", "Alle Kategorien"),
    "Make": ("Marka", "Marke"),
    "Details and downloads are available to subscribers.": ("Szczegóły i pliki są dostępne dla subskrybentów.", "Details und Downloads sind Abonnenten vorbehalten."),
    "by": ("autor:", "von"),
    "deleted user": ("usunięty użytkownik", "gelöschter Nutzer"),
    "Power": ("Moc", "Leistung"),
    "Torque": ("Moment obrotowy", "Drehmoment"),
    "Attachments": ("Załączniki", "Anhänge"),
    "Comments": ("Komentarze", "Kommentare"),
    "Add comment": ("Dodaj komentarz", "Kommentar hinzufügen"),
    "Report this entry": ("Zgłoś ten wpis", "Diesen Eintrag melden"),
    "Send report": ("Wyślij zgłoszenie", "Meldung senden"),
    "Publish": ("Opublikuj", "Veröffentlichen"),
    "Do not publish content intended to defeat emission-control systems or illegal for road use. Only share what you have the right to share.":
        ("Nie publikuj treści służących do wyłączania układów ograniczających emisje ani niezgodnych z prawem o ruchu drogowym. Udostępniaj tylko to, do czego masz prawa.",
         "Veröffentliche keine Inhalte zur Umgehung von Abgasreinigungssystemen oder die für den Straßenverkehr unzulässig sind. Teile nur, wozu du berechtigt bist."),
    "Save": ("Zapisz", "Speichern"),
    # models / forms / views
    "Modification": ("Modyfikacja", "Modifikation"),
    "Engine map (ECU)": ("Mapa silnika (ECU)", "Motorkennfeld (ECU)"),
    "Gearbox map (TCU)": ("Mapa skrzyni biegów (TCU)", "Getriebekennfeld (TCU)"),
    "Turbocharger settings": ("Ustawienia turbosprężarki", "Turbolader-Einstellungen"),
    "Other": ("Inne", "Sonstiges"),
    "Published": ("Opublikowany", "Veröffentlicht"),
    "Hidden by moderator": ("Ukryty przez moderatora", "Vom Moderator ausgeblendet"),
    "title": ("tytuł", "Titel"),
    "engine / code": ("silnik / kod", "Motor / Code"),
    "gearbox": ("skrzynia biegów", "Getriebe"),
    "description": ("opis", "Beschreibung"),
    "email": ("e-mail", "E-Mail"),
    "nickname": ("pseudonim", "Spitzname"),
    "Email": ("E-mail", "E-Mail"),
    "Password": ("Hasło", "Passwort"),
    "Incorrect password.": ("Nieprawidłowe hasło.", "Falsches Passwort."),
    "This email cannot be used.": ("Tego adresu e-mail nie można użyć.", "Diese E-Mail kann nicht verwendet werden."),
    "I accept the Terms of Service": ("Akceptuję Regulamin", "Ich akzeptiere die Nutzungsbedingungen"),
    "I have read the Privacy Policy": ("Zapoznałem(-am) się z Polityką prywatności", "Ich habe die Datenschutzerklärung gelesen"),
    "I agree to receive product news by email (optional)": ("Zgadzam się na otrzymywanie nowości e-mailem (opcjonalnie)", "Ich möchte Produktneuigkeiten per E-Mail erhalten (optional)"),
    "Please confirm your email address first (check your inbox).": ("Najpierw potwierdź adres e-mail (sprawdź skrzynkę).", "Bitte bestätige zuerst deine E-Mail-Adresse (Posteingang prüfen)."),
    "Attachment (map, log, photo)": ("Załącznik (mapa, log, zdjęcie)", "Anhang (Kennfeld, Log, Foto)"),
    "File type not allowed. Allowed: %(types)s": ("Niedozwolony typ pliku. Dozwolone: %(types)s", "Dateityp nicht erlaubt. Erlaubt: %(types)s"),
    "File too large.": ("Plik jest za duży.", "Datei ist zu groß."),
    "Confirm your email address": ("Potwierdź adres e-mail", "Bestätige deine E-Mail-Adresse"),
    "Welcome! Confirm your email by opening this link (valid 48 hours):\n%(link)s":
        ("Witamy! Potwierdź adres e-mail, otwierając ten link (ważny 48 godzin):\n%(link)s",
         "Willkommen! Bestätige deine E-Mail über diesen Link (48 Stunden gültig):\n%(link)s"),
    "This confirmation link is invalid or has expired.": ("Link potwierdzający jest nieprawidłowy lub wygasł.", "Der Bestätigungslink ist ungültig oder abgelaufen."),
    "Email confirmed. Welcome!": ("Adres e-mail potwierdzony. Witamy!", "E-Mail bestätigt. Willkommen!"),
    "Your account has been deleted.": ("Twoje konto zostało usunięte.", "Dein Konto wurde gelöscht."),
    "Entry published.": ("Wpis opublikowany.", "Eintrag veröffentlicht."),
    "Thank you. A moderator will review your report.": ("Dziękujemy. Moderator rozpatrzy zgłoszenie.", "Danke. Ein Moderator prüft deine Meldung."),
    "An active subscription is required to view this content.": ("Do wyświetlenia tej treści wymagana jest aktywna subskrypcja.", "Für diesen Inhalt ist ein aktives Abonnement erforderlich."),
    "Confirm your email address first.": ("Najpierw potwierdź adres e-mail.", "Bestätige zuerst deine E-Mail-Adresse."),
    "You (or someone else) requested a password reset. Open this link to choose a new password:":
        ("Ty (lub ktoś inny) poprosił o reset hasła. Otwórz ten link, aby ustawić nowe hasło:",
         "Du (oder jemand anderes) hast ein Zurücksetzen des Passworts angefordert. Öffne diesen Link, um ein neues Passwort festzulegen:"),
    # legal placeholders
    "TEMPLATE: this text is a placeholder and must be replaced with terms prepared by a lawyer before launch.":
        ("SZABLON: ten tekst jest tymczasowy i przed startem musi zostać zastąpiony regulaminem przygotowanym przez prawnika.",
         "VORLAGE: Dieser Text ist ein Platzhalter und muss vor dem Start durch von einem Juristen erstellte Bedingungen ersetzt werden."),
    "TEMPLATE: this text is a placeholder and must be replaced with a policy prepared by a lawyer (controller identity, legal bases, retention, processors) before launch.":
        ("SZABLON: ten tekst jest tymczasowy i przed startem musi zostać zastąpiony polityką przygotowaną przez prawnika (administrator, podstawy prawne, retencja, podmioty przetwarzające).",
         "VORLAGE: Dieser Text ist ein Platzhalter und muss vor dem Start durch eine von einem Juristen erstellte Erklärung ersetzt werden (Verantwortlicher, Rechtsgrundlagen, Speicherdauer, Auftragsverarbeiter)."),
    "Access to the service requires a paid subscription ($5 per month, billed monthly, cancellable at any time in the customer portal).":
        ("Dostęp do serwisu wymaga płatnej subskrypcji (5 $ miesięcznie, rozliczana miesięcznie, można ją anulować w dowolnym momencie w portalu klienta).",
         "Der Zugang erfordert ein kostenpflichtiges Abonnement (5 $ pro Monat, monatliche Abrechnung, jederzeit im Kundenportal kündbar)."),
    "Users are responsible for the content they publish and confirm they have the right to share it.":
        ("Użytkownicy odpowiadają za publikowane treści i potwierdzają, że mają prawo je udostępniać.",
         "Nutzer sind für ihre Inhalte verantwortlich und bestätigen, dass sie zur Weitergabe berechtigt sind."),
    "Content intended to defeat emission-control systems (DPF, EGR, AdBlue/SCR, catalytic converters) or for road use contrary to local law is prohibited.":
        ("Zabronione są treści służące do wyłączania układów ograniczających emisje (DPF, EGR, AdBlue/SCR, katalizatory) lub sprzeczne z lokalnym prawem o ruchu drogowym.",
         "Inhalte zur Umgehung von Abgasreinigungssystemen (DPF, AGR, AdBlue/SCR, Katalysatoren) oder für eine nach lokalem Recht unzulässige Straßennutzung sind verboten."),
    "Modifications are made at your own risk. Information is provided as is, without any warranty.":
        ("Modyfikacje wykonujesz na własne ryzyko. Informacje udostępniamy w stanie „takim, jakim są”, bez gwarancji.",
         "Modifikationen erfolgen auf eigenes Risiko. Informationen werden ohne jegliche Gewähr bereitgestellt."),
    "We may remove content and suspend accounts that violate these terms.":
        ("Możemy usuwać treści i zawieszać konta naruszające regulamin.",
         "Wir können Inhalte entfernen und Konten sperren, die gegen diese Bedingungen verstoßen."),
    "We collect only: email, nickname, language, consent records and your content.":
        ("Zbieramy tylko: e-mail, pseudonim, język, zapisy zgód i Twoje treści.",
         "Wir erheben nur: E-Mail, Spitzname, Sprache, Einwilligungsnachweise und deine Inhalte."),
    "Payments are processed by Stripe; we never see or store your card number.":
        ("Płatności obsługuje Stripe; nigdy nie widzimy ani nie przechowujemy numeru Twojej karty.",
         "Zahlungen werden von Stripe abgewickelt; wir sehen oder speichern deine Kartennummer nie."),
    "We use only essential cookies (session, security, language). No advertising or analytics trackers.":
        ("Używamy wyłącznie niezbędnych plików cookie (sesja, bezpieczeństwo, język). Bez reklam i trackerów analitycznych.",
         "Wir verwenden nur notwendige Cookies (Sitzung, Sicherheit, Sprache). Keine Werbe- oder Analyse-Tracker."),
    "You can download all your data or delete your account at any time in your account settings.":
        ("W ustawieniach konta w każdej chwili możesz pobrać wszystkie swoje dane lub usunąć konto.",
         "In den Kontoeinstellungen kannst du jederzeit alle Daten herunterladen oder dein Konto löschen."),
}

# ---- v2: community features, new UI ------------------------------------------------------
T.update({
    # accounts
    "Language for emails": ("Język wiadomości e-mail", "Sprache für E-Mails"),
    "This nickname is already taken.": ("Ten pseudonim jest już zajęty.", "Dieser Spitzname ist bereits vergeben."),
    "Use 3–30 characters: letters, digits, dot, dash or underscore.":
        ("Użyj 3–30 znaków: liter, cyfr, kropki, myślnika lub podkreślnika.", "Verwende 3–30 Zeichen: Buchstaben, Ziffern, Punkt, Bindestrich oder Unterstrich."),
    "3–30 characters: letters, digits, dot, dash, underscore. Visible publicly.":
        ("3–30 znaków: litery, cyfry, kropka, myślnik, podkreślnik. Widoczny publicznie.", "3–30 Zeichen: Buchstaben, Ziffern, Punkt, Bindestrich, Unterstrich. Öffentlich sichtbar."),
    "about me": ("o mnie", "über mich"),
    "email me about comments on my entries": ("powiadamiaj mnie e-mailem o komentarzach do moich wpisów", "per E-Mail über Kommentare zu meinen Einträgen informieren"),
    "Resend confirmation email": ("Wyślij ponownie e-mail potwierdzający", "Bestätigungs-E-Mail erneut senden"),
    "Send": ("Wyślij", "Senden"),
    "Changes saved.": ("Zmiany zapisane.", "Änderungen gespeichert."),
    "Profile": ("Profil", "Profil"),
    "View public profile": ("Zobacz profil publiczny", "Öffentliches Profil ansehen"),
    "Security": ("Bezpieczeństwo", "Sicherheit"),
    "Last login": ("Ostatnie logowanie", "Letzte Anmeldung"),
    "You can download everything we store about you, or erase your account at any time.":
        ("W każdej chwili możesz pobrać wszystko, co o Tobie przechowujemy, lub usunąć konto.", "Du kannst jederzeit alle über dich gespeicherten Daten herunterladen oder dein Konto löschen."),
    "Cancel": ("Anuluj", "Abbrechen"),
    "Didn't get the confirmation email?": ("Nie dotarł e-mail potwierdzający?", "Keine Bestätigungs-E-Mail erhalten?"),
    "New here?": ("Pierwszy raz tutaj?", "Neu hier?"),
    "Member since": ("Członek od", "Mitglied seit"),
    "entries": ("wpisów", "Einträge"),
    "helpful votes": ("głosów „pomocne”", "hilfreich-Stimmen"),
    "Entries": ("Wpisy", "Einträge"),
    "We only ask for an email and a nickname. Your real name is never required.":
        ("Prosimy tylko o e-mail i pseudonim. Nigdy nie wymagamy imienia i nazwiska.", "Wir fragen nur nach E-Mail und Spitzname. Dein echter Name wird nie benötigt."),
    "Already have an account?": ("Masz już konto?", "Schon ein Konto?"),
    "Account settings": ("Ustawienia konta", "Kontoeinstellungen"),
    "My profile": ("Mój profil", "Mein Profil"),
    "My entries": ("Moje wpisy", "Meine Einträge"),
    "Saved entries": ("Zapisane wpisy", "Gespeicherte Einträge"),
    "Account menu": ("Menu konta", "Kontomenü"),
    "Moderation panel": ("Panel moderacji", "Moderationsbereich"),
    # billing
    "Test subscription activated (development mode).": ("Testowa subskrypcja aktywowana (tryb deweloperski).", "Test-Abonnement aktiviert (Entwicklungsmodus)."),
    "Test subscription cancelled (development mode).": ("Testowa subskrypcja anulowana (tryb deweloperski).", "Test-Abonnement gekündigt (Entwicklungsmodus)."),
    "Payments are not configured yet. Please try again later.": ("Płatności nie są jeszcze skonfigurowane. Spróbuj później.", "Zahlungen sind noch nicht eingerichtet. Bitte später erneut versuchen."),
    "The payment provider is temporarily unavailable. Please try again.": ("Operator płatności jest chwilowo niedostępny. Spróbuj ponownie.", "Der Zahlungsanbieter ist vorübergehend nicht erreichbar. Bitte erneut versuchen."),
    "Active": ("Aktywna", "Aktiv"),
    "Access until": ("Dostęp do", "Zugang bis"),
    "Renews on": ("Odnowienie", "Verlängerung am"),
    "Cancel test subscription": ("Anuluj testową subskrypcję", "Test-Abonnement kündigen"),
    "Activate test subscription": ("Aktywuj testową subskrypcję", "Test-Abonnement aktivieren"),
    "One plan. Everything included.": ("Jeden plan. Wszystko w cenie.", "Ein Tarif. Alles inklusive."),
    "No ads, no data selling – the community is funded by members.": ("Bez reklam i handlu danymi – społeczność utrzymują członkowie.", "Keine Werbung, kein Datenverkauf – die Community wird von Mitgliedern finanziert."),
    "Comments, helpful votes and saved entries": ("Komentarze, głosy i zapisane wpisy", "Kommentare, Bewertungen und gespeicherte Einträge"),
    "Content in Polish, English and German": ("Treści po polsku, angielsku i niemiecku", "Inhalte auf Polnisch, Englisch und Deutsch"),
    "Development mode": ("Tryb deweloperski", "Entwicklungsmodus"),
    "Stripe keys are not configured, so you can simulate a subscription to test the paid features locally. This button is disabled in production.":
        ("Klucze Stripe nie są skonfigurowane, więc możesz zasymulować subskrypcję, aby lokalnie przetestować płatne funkcje. Na produkcji ten przycisk jest wyłączony.",
         "Stripe-Schlüssel sind nicht konfiguriert, daher kannst du ein Abonnement simulieren, um die kostenpflichtigen Funktionen lokal zu testen. In Produktion ist diese Schaltfläche deaktiviert."),
    "Questions": ("Pytania", "Fragen"),
    "Can I cancel any time?": ("Czy mogę zrezygnować w każdej chwili?", "Kann ich jederzeit kündigen?"),
    "Yes. Cancel in the billing portal; access stays until the end of the paid period.":
        ("Tak. Anulujesz w portalu płatności; dostęp zostaje do końca opłaconego okresu.", "Ja. Kündige im Abrechnungsportal; der Zugang bleibt bis zum Ende des bezahlten Zeitraums."),
    "Do you store my card?": ("Czy przechowujecie moją kartę?", "Speichert ihr meine Karte?"),
    "No. Payments are handled by Stripe; we never see your card number.":
        ("Nie. Płatności obsługuje Stripe; nigdy nie widzimy numeru Twojej karty.", "Nein. Zahlungen laufen über Stripe; wir sehen deine Kartennummer nie."),
    "Do I get an invoice?": ("Czy dostanę fakturę?", "Bekomme ich eine Rechnung?"),
    "Yes, every payment comes with an invoice. Business customers can enter a VAT ID at checkout.":
        ("Tak, każda płatność ma fakturę. Firmy mogą podać NIP przy płatności.", "Ja, zu jeder Zahlung gibt es eine Rechnung. Geschäftskunden können beim Bezahlen eine USt-IdNr. angeben."),
    "Pricing": ("Cennik", "Preise"),
    # catalog: models & forms
    "This file looks like an executable and cannot be uploaded.": ("Ten plik wygląda na program wykonywalny i nie może zostać przesłany.", "Diese Datei sieht wie ein Programm aus und kann nicht hochgeladen werden."),
    "Attachments (maps, logs, photos)": ("Załączniki (mapy, logi, zdjęcia)", "Anhänge (Kennfelder, Logs, Fotos)"),
    "Up to %(n)s files, max %(mb)s MB each.": ("Do %(n)s plików, maks. %(mb)s MB każdy.", "Bis zu %(n)s Dateien, max. %(mb)s MB pro Datei."),
    "Newest": ("Najnowsze", "Neueste"),
    "Most helpful": ("Najbardziej pomocne", "Hilfreichste"),
    "Most discussed": ("Najczęściej komentowane", "Meistdiskutiert"),
    "Model": ("Model", "Modell"),
    "All models": ("Wszystkie modele", "Alle Modelle"),
    "All makes": ("Wszystkie marki", "Alle Marken"),
    "Category": ("Kategoria", "Kategorie"),
    "Sort": ("Sortuj", "Sortieren"),
    "The image file is damaged or not an image.": ("Plik obrazu jest uszkodzony lub nie jest obrazem.", "Die Bilddatei ist beschädigt oder kein Bild."),
    "Too many attachments (max %(n)s per entry).": ("Za dużo załączników (maks. %(n)s na wpis).", "Zu viele Anhänge (max. %(n)s pro Eintrag)."),
    "This value looks unrealistic. Please double-check.": ("Ta wartość wygląda nierealnie. Sprawdź ją.", "Dieser Wert wirkt unrealistisch. Bitte prüfen."),
    "e.g. Boost target @ 4000 rpm": ("np. Doładowanie przy 4000 obr./min", "z. B. Ladedruck bei 4000 U/min"),
    "Title, engine, ECU, turbo…": ("Tytuł, silnik, ECU, turbo…", "Titel, Motor, Steuergerät, Turbo…"),
    "Any fuel": ("Dowolne paliwo", "Jeder Kraftstoff"),
    "Any stage": ("Dowolny stage", "Jede Stufe"),
    "Any language": ("Dowolny język", "Jede Sprache"),
    "category": ("kategoria", "Kategorie"),
    "content language": ("język treści", "Sprache des Inhalts"),
    "model year": ("rok modelowy", "Modelljahr"),
    "fuel": ("paliwo", "Kraftstoff"),
    "stage": ("stage", "Stufe"),
    "turbocharger": ("turbosprężarka", "Turbolader"),
    "peak boost (bar)": ("maks. doładowanie (bar)", "max. Ladedruck (bar)"),
    "power before (hp)": ("moc przed (KM)", "Leistung vorher (PS)"),
    "power after (hp)": ("moc po (KM)", "Leistung nachher (PS)"),
    "torque before (Nm)": ("moment przed (Nm)", "Drehmoment vorher (Nm)"),
    "torque after (Nm)": ("moment po (Nm)", "Drehmoment nachher (Nm)"),
    "parameter": ("parametr", "Parameter"),
    "value": ("wartość", "Wert"),
    "unit": ("jednostka", "Einheit"),
    "comment": ("komentarz", "Kommentar"),
    "reason": ("powód", "Grund"),
    "car": ("samochód", "Fahrzeug"),
    "Petrol": ("Benzyna", "Benzin"),
    "Diesel": ("Diesel", "Diesel"),
    "Hybrid": ("Hybryda", "Hybrid"),
    "LPG": ("LPG", "Autogas (LPG)"),
    "E85 / flex fuel": ("E85 / flex fuel", "E85 / Flex-Fuel"),
    "Electric": ("Elektryczny", "Elektrisch"),
    "Stock / reference": ("Seria / referencja", "Serie / Referenz"),
    "Stage 1": ("Stage 1", "Stufe 1"),
    "Stage 2": ("Stage 2", "Stufe 2"),
    "Stage 3+": ("Stage 3+", "Stufe 3+"),
    "Custom": ("Indywidualny", "Individuell"),
    "e.g. 2.0 TFSI EA888 Gen3": ("np. 2.0 TFSI EA888 Gen3", "z. B. 2.0 TFSI EA888 Gen3"),
    "e.g. Bosch MED17.5": ("np. Bosch MED17.5", "z. B. Bosch MED17.5"),
    "e.g. DQ250 DSG, ZF 8HP": ("np. DQ250 DSG, ZF 8HP", "z. B. DQ250 DSG, ZF 8HP"),
    "e.g. IHI IS38, Garrett GTX3076R": ("np. IHI IS38, Garrett GTX3076R", "z. B. IHI IS38, Garrett GTX3076R"),
    # catalog: views
    "Attachment removed.": ("Załącznik usunięty.", "Anhang entfernt."),
    "Entry deleted.": ("Wpis usunięty.", "Eintrag gelöscht."),
    "New comment on “%(title)s”": ("Nowy komentarz do „%(title)s”", "Neuer Kommentar zu „%(title)s“"),
    "%(user)s commented on your entry:\n\n%(body)s\n\n%(link)s\n\nYou can turn these emails off in your account settings.":
        ("%(user)s skomentował(a) Twój wpis:\n\n%(body)s\n\n%(link)s\n\nMożesz wyłączyć te wiadomości w ustawieniach konta.",
         "%(user)s hat deinen Eintrag kommentiert:\n\n%(body)s\n\n%(link)s\n\nDu kannst diese E-Mails in den Kontoeinstellungen abschalten."),
    "You have already reported this entry.": ("Ten wpis został już przez Ciebie zgłoszony.", "Du hast diesen Eintrag bereits gemeldet."),
    "You cannot vote for your own entry.": ("Nie możesz głosować na własny wpis.", "Du kannst nicht für deinen eigenen Eintrag stimmen."),
    # error pages
    "Session expired": ("Sesja wygasła", "Sitzung abgelaufen"),
    "For your security the form could not be submitted. Go back, refresh the page and try again.":
        ("Ze względów bezpieczeństwa formularz nie został wysłany. Wróć, odśwież stronę i spróbuj ponownie.", "Aus Sicherheitsgründen konnte das Formular nicht gesendet werden. Gehe zurück, lade die Seite neu und versuche es erneut."),
    "Home": ("Strona główna", "Startseite"),
    "Page not found": ("Nie znaleziono strony", "Seite nicht gefunden"),
    "The page may have been moved, hidden by a moderator or never existed.":
        ("Strona mogła zostać przeniesiona, ukryta przez moderatora lub nigdy nie istniała.", "Die Seite wurde verschoben, von einem Moderator ausgeblendet oder hat nie existiert."),
    "Browse the library": ("Przeglądaj bibliotekę", "Bibliothek durchsuchen"),
    "Too many requests": ("Zbyt wiele żądań", "Zu viele Anfragen"),
    "Please wait a few minutes and try again.": ("Odczekaj kilka minut i spróbuj ponownie.", "Bitte warte ein paar Minuten und versuche es erneut."),
    # layout
    "Pages": ("Strony", "Seiten"),
    "Previous": ("Poprzednia", "Zurück"),
    "Next": ("Następna", "Weiter"),
    "Tuning community": ("Społeczność tuningowa", "Tuning-Community"),
    "Skip to content": ("Przejdź do treści", "Zum Inhalt springen"),
    "Development mode – demo data, emails printed to the console, payments simulated.":
        ("Tryb deweloperski – dane demo, e-maile w konsoli, płatności symulowane.", "Entwicklungsmodus – Demodaten, E-Mails in der Konsole, Zahlungen simuliert."),
    "Main": ("Główna nawigacja", "Hauptnavigation"),
    "Makes": ("Marki", "Marken"),
    "Built by tuners, for tuners.": ("Tworzone przez tunerów, dla tunerów.", "Von Tunern, für Tuner."),
    # detail
    "Helpful": ("Pomocne", "Hilfreich"),
    "Saved": ("Zapisano", "Gespeichert"),
    "Edit": ("Edytuj", "Bearbeiten"),
    "Delete": ("Usuń", "Löschen"),
    "Helpful votes": ("Głosy „pomocne”", "Hilfreich-Stimmen"),
    "hp": ("KM", "PS"),
    "Peak boost": ("Maks. doładowanie", "Max. Ladedruck"),
    "Description": ("Opis", "Beschreibung"),
    "Settings & parameters": ("Ustawienia i parametry", "Einstellungen & Parameter"),
    "Parameter": ("Parametr", "Parameter"),
    "Value": ("Wartość", "Wert"),
    "Files are shared by members. Always verify maps (checksums, logs) before flashing – at your own risk.":
        ("Pliki udostępniają członkowie. Zawsze weryfikuj mapy (sumy kontrolne, logi) przed wgraniem – na własne ryzyko.",
         "Dateien werden von Mitgliedern geteilt. Prüfe Kennfelder (Prüfsummen, Logs) immer vor dem Flashen – auf eigenes Risiko."),
    "Delete this comment?": ("Usunąć ten komentarz?", "Diesen Kommentar löschen?"),
    "No comments yet. Ask a question or share your results.": ("Brak komentarzy. Zadaj pytanie lub podziel się wynikami.", "Noch keine Kommentare. Stell eine Frage oder teile deine Ergebnisse."),
    "This entry is available to subscribers": ("Ten wpis jest dostępny dla subskrybentów", "Dieser Eintrag ist für Abonnenten verfügbar"),
    "Full description, %(p)s parameters, %(a)s attachments and %(c)s comments.":
        ("Pełny opis, parametry: %(p)s, załączniki: %(a)s, komentarze: %(c)s.", "Vollständige Beschreibung, Parameter: %(p)s, Anhänge: %(a)s, Kommentare: %(c)s."),
    "Specification": ("Specyfikacja", "Spezifikation"),
    "Car": ("Samochód", "Fahrzeug"),
    "Model year": ("Rok modelowy", "Modelljahr"),
    "Engine": ("Silnik", "Motor"),
    "Fuel": ("Paliwo", "Kraftstoff"),
    "ECU": ("ECU", "Steuergerät (ECU)"),
    "Gearbox": ("Skrzynia biegów", "Getriebe"),
    "Turbo": ("Turbo", "Turbo"),
    "Stage": ("Stage", "Stufe"),
    "Updated": ("Zaktualizowano", "Aktualisiert"),
    "More for this car": ("Więcej dla tego auta", "Mehr zu diesem Fahrzeug"),
    "Illegal content (e.g. emission-control removal), copyright infringement, dangerous or abusive content.":
        ("Treści nielegalne (np. usuwanie układów emisji), naruszenie praw autorskich, treści niebezpieczne lub obraźliwe.",
         "Illegale Inhalte (z. B. Entfernen der Abgasreinigung), Urheberrechtsverletzungen, gefährliche oder beleidigende Inhalte."),
    # form
    "Edit entry": ("Edytuj wpis", "Eintrag bearbeiten"),
    "Basics": ("Podstawowe informacje", "Grunddaten"),
    "Missing your car? Let us know via the report link and a moderator will add it.":
        ("Brakuje Twojego auta? Daj znać przez zgłoszenie, a moderator je doda.", "Dein Fahrzeug fehlt? Gib uns über die Melden-Funktion Bescheid, ein Moderator fügt es hinzu."),
    "Hardware": ("Sprzęt", "Hardware"),
    "Results": ("Wyniki", "Ergebnisse"),
    "What did you change, on what fuel, with which supporting mods? Logs and lessons learned help others most.":
        ("Co zmieniłeś, na jakim paliwie, z jakimi modyfikacjami? Logi i wnioski najbardziej pomagają innym.",
         "Was hast du geändert, mit welchem Kraftstoff und welchen Begleitmaßnahmen? Logs und Erfahrungen helfen anderen am meisten."),
    "Structured values such as boost targets, torque limits or shift points.":
        ("Wartości strukturalne, np. doładowanie, limity momentu, punkty zmiany biegów.", "Strukturierte Werte wie Ladedruck, Drehmomentgrenzen oder Schaltpunkte."),
    "Unit": ("Jednostka", "Einheit"),
    "remove": ("usuń", "entfernen"),
    "Add parameter": ("Dodaj parametr", "Parameter hinzufügen"),
    "Remove": ("Usuń", "Entfernen"),
    "Save changes": ("Zapisz zmiany", "Änderungen speichern"),
    "Remove this attachment?": ("Usunąć ten załącznik?", "Diesen Anhang entfernen?"),
    "Delete entry": ("Usuń wpis", "Eintrag löschen"),
    "Delete “%(title)s” together with its parameters, attachments, comments and votes? This cannot be undone.":
        ("Usunąć „%(title)s” razem z parametrami, załącznikami, komentarzami i głosami? Tej operacji nie można cofnąć.",
         "„%(title)s“ samt Parametern, Anhängen, Kommentaren und Stimmen löschen? Dies kann nicht rückgängig gemacht werden."),
    "Nothing here yet.": ("Na razie nic tu nie ma.", "Hier ist noch nichts."),
    # list / makes
    "Filters": ("Filtry", "Filter"),
    "Clear": ("Wyczyść", "Zurücksetzen"),
    "Clear filters": ("Wyczyść filtry", "Filter zurücksetzen"),
    "Browse entries by manufacturer.": ("Przeglądaj wpisy według producenta.", "Einträge nach Hersteller durchsuchen."),
    "No makes yet.": ("Brak marek.", "Noch keine Marken."),
    # landing
    "Tuning community: maps, settings, modifications": ("Społeczność tuningowa: mapy, ustawienia, modyfikacje", "Tuning-Community: Kennfelder, Einstellungen, Modifikationen"),
    "For tuners, by tuners": ("Od tunerów, dla tunerów", "Von Tunern, für Tuner"),
    "Share your setup": ("Podziel się swoim setupem", "Teile dein Setup"),
    "makes": ("marek", "Marken"),
    "members": ("członków", "Mitglieder"),
    "Engine maps (ECU)": ("Mapy silnika (ECU)", "Motorkennfelder (ECU)"),
    "Boost, ignition and fuel tables with before/after numbers.": ("Doładowanie, zapłon i dawka paliwa z wynikami przed/po.", "Ladedruck-, Zünd- und Kraftstofftabellen mit Vorher/Nachher-Werten."),
    "Gearbox maps (TCU)": ("Mapy skrzyń (TCU)", "Getriebekennfelder (TCU)"),
    "Torque limits, shift points and clutch pressures.": ("Limity momentu, punkty zmiany biegów i docisk sprzęgieł.", "Drehmomentgrenzen, Schaltpunkte und Kupplungsdrücke."),
    "Turbo settings": ("Ustawienia turbo", "Turbo-Einstellungen"),
    "Boost curves, wastegate and turbo upgrades.": ("Krzywe doładowania, wastegate i większe turbiny.", "Ladedruckkurven, Wastegate und Turbo-Upgrades."),
    "Modifications": ("Modyfikacje", "Modifikationen"),
    "Hardware, maintenance and measured results.": ("Sprzęt, serwis i zmierzone wyniki.", "Hardware, Wartung und gemessene Ergebnisse."),
    "Popular makes": ("Popularne marki", "Beliebte Marken"),
    "How it works": ("Jak to działa", "So funktioniert's"),
    "Create an account": ("Załóż konto", "Konto erstellen"),
    "Confirm your email – we only store what is necessary.": ("Potwierdź e-mail – przechowujemy tylko to, co niezbędne.", "Bestätige deine E-Mail – wir speichern nur das Nötigste."),
    "Subscribe for $5 / month": ("Subskrybuj za 5 $ / miesiąc", "Abonniere für 5 $ / Monat"),
    "Secure payment by Stripe. Cancel any time in one click.": ("Bezpieczna płatność przez Stripe. Rezygnacja jednym kliknięciem.", "Sichere Zahlung über Stripe. Mit einem Klick kündbar."),
    "Share and learn": ("Dziel się i ucz", "Teilen und lernen"),
    "Download maps, compare settings and vote for the most helpful entries.": ("Pobieraj mapy, porównuj ustawienia i głosuj na najlepsze wpisy.", "Lade Kennfelder herunter, vergleiche Einstellungen und stimme für die hilfreichsten Einträge."),
    "Ready to unlock every map and setting?": ("Gotowy na dostęp do wszystkich map i ustawień?", "Bereit für alle Kennfelder und Einstellungen?"),
    "Full access to the library, attachments and the community.": ("Pełny dostęp do biblioteki, załączników i społeczności.", "Voller Zugang zu Bibliothek, Anhängen und Community."),
})
T.update({
    "An account with this email already exists. If it is yours, log in or reset your password.":
        ("Konto z tym adresem już istnieje. Jeśli należy do Ciebie, zaloguj się lub zresetuj hasło.",
         "Ein Konto mit dieser E-Mail existiert bereits. Wenn es deins ist, melde dich an oder setze dein Passwort zurück."),
    "Your email address is already confirmed. Please log in.": ("Twój adres e-mail jest już potwierdzony. Zaloguj się.", "Deine E-Mail-Adresse ist bereits bestätigt. Bitte melde dich an."),
    "Email confirmed. You can now log in.": ("Adres e-mail potwierdzony. Możesz się zalogować.", "E-Mail bestätigt. Du kannst dich jetzt anmelden."),
    "Your last payment failed. Please update your payment method in the billing portal.":
        ("Ostatnia płatność nie powiodła się. Zaktualizuj metodę płatności w portalu płatności.", "Deine letzte Zahlung ist fehlgeschlagen. Bitte aktualisiere deine Zahlungsmethode im Abrechnungsportal."),
    "The end year must not be earlier than the start year.": ("Rok końcowy nie może być wcześniejszy niż początkowy.", "Das Endjahr darf nicht vor dem Startjahr liegen."),
    "make": ("marka", "Marke"),
    "model": ("model", "Modell"),
    "generation / code": ("generacja / kod", "Generation / Code"),
    "from year": ("od roku", "ab Jahr"),
    "to year": ("do roku", "bis Jahr"),
    "e.g. B8, E46, MK7": ("np. B8, E46, MK7", "z. B. B8, E46, MK7"),
    "Thank you! A moderator will add the car to the catalogue soon.": ("Dziękujemy! Moderator wkrótce doda auto do katalogu.", "Danke! Ein Moderator fügt das Fahrzeug bald zum Katalog hinzu."),
    "Suggest a missing car": ("Zaproponuj brakujące auto", "Fehlendes Fahrzeug vorschlagen"),
    "Send suggestion": ("Wyślij propozycję", "Vorschlag senden"),
    "Missing your car? Suggest it and a moderator will add it.": ("Brakuje Twojego auta? Zaproponuj je, a moderator je doda.", "Dein Fahrzeug fehlt? Schlag es vor, ein Moderator fügt es hinzu."),
})
for _obsolete in ("Attachment (map, log, photo)", "My account", "by", "renews/ends", "Email confirmed. Welcome!",
                  "Missing your car? Let us know via the report link and a moderator will add it.", "This email cannot be used."):
    T.pop(_obsolete, None)

# Plural messages: (singular, plural) -> ([pl one, few, many], [de one, other])
P = {
    ("%(counter)s entry", "%(counter)s entries"): (
        ["%(counter)s wpis", "%(counter)s wpisy", "%(counter)s wpisów"],
        ["%(counter)s Eintrag", "%(counter)s Einträge"],
    ),
    ("%(counter)s download", "%(counter)s downloads"): (
        ["%(counter)s pobranie", "%(counter)s pobrania", "%(counter)s pobrań"],
        ["%(counter)s Download", "%(counter)s Downloads"],
    ),
}

PLURAL_FORMS = {
    "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
    "de": "nplurals=2; plural=(n != 1);",
}


def build(lang_idx: int, lang: str) -> None:
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "tunehub",
        "Language": lang,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": PLURAL_FORMS[lang],
    }
    for msgid, tr in T.items():
        po.append(polib.POEntry(msgid=msgid, msgstr=tr[lang_idx]))
    for (singular, plural), forms in P.items():
        po.append(polib.POEntry(
            msgid=singular, msgid_plural=plural, msgstr_plural=dict(enumerate(forms[lang_idx]))
        ))
    out = ROOT / "locale" / lang / "LC_MESSAGES"
    out.mkdir(parents=True, exist_ok=True)
    po.save(str(out / "django.po"))
    po.save_as_mofile(str(out / "django.mo"))
    print(f"{lang}: {len(po)} messages")


if __name__ == "__main__":
    build(0, "pl")
    build(1, "de")
