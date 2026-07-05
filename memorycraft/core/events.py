"""Event-type registry.

Every occasion carries its own design language: default theme, palette
accent, opening/closing copy, pacing and music mood. The generators read
this registry so adding a new occasion is a one-entry change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventProfile:
    name: str
    emoji: str
    default_theme: str
    opening_line: str              # {honoree}/{title} placeholders allowed
    closing_line: str
    music_mood: str                # suggestion surfaced in the UI
    pace: float = 1.0              # multiplier on per-photo duration
    quote: str = ""                # signature quote used when user adds none
    subtitle: str = ""


EVENTS: dict[str, EventProfile] = {p.name: p for p in [
    EventProfile("Birthday", "🎂", "Kids",
                 "Happy Birthday, {honoree}!",
                 "Wishing you many more beautiful years",
                 "Upbeat pop / feel-good acoustic", 0.9,
                 "Count your life by smiles, not tears.",
                 "A celebration of another wonderful year"),
    EventProfile("Wedding", "💍", "Elegant Gold",
                 "{honoree}",
                 "And so the adventure begins…",
                 "Romantic piano / strings", 1.15,
                 "Two souls, one heart.",
                 "The beginning of forever"),
    EventProfile("Wedding Anniversary", "💞", "Royal",
                 "Happy Anniversary, {honoree}",
                 "Here's to a love that grows every year",
                 "Soft jazz / romantic classics", 1.1,
                 "Love grows more precious with time."),
    EventProfile("Silver Jubilee", "🥈", "Classic",
                 "25 Wonderful Years",
                 "A silver milestone of togetherness",
                 "Elegant orchestral", 1.1,
                 "Twenty-five years of shared sunrises."),
    EventProfile("Golden Jubilee", "🏅", "Luxury",
                 "50 Golden Years",
                 "A lifetime of love, honoured today",
                 "Warm orchestral / nostalgic classics", 1.2,
                 "Fifty years, and still counting the stars."),
    EventProfile("Graduation", "🎓", "Modern",
                 "Congratulations, {honoree}!",
                 "The tassel was worth the hassle",
                 "Inspiring / cinematic build-up", 0.95,
                 "The future belongs to those who believe in their dreams."),
    EventProfile("Baby Shower", "🍼", "Floral",
                 "Welcome, little {honoree}",
                 "A tiny miracle, a lifetime of love",
                 "Gentle lullaby / soft acoustic", 1.05,
                 "First we had each other, now we have everything."),
    EventProfile("House Warming", "🏡", "Minimal",
                 "Welcome to our new home",
                 "May these walls hold a lifetime of laughter",
                 "Warm acoustic folk", 1.0,
                 "Home is where our story begins."),
    EventProfile("Family Reunion", "👨‍👩‍👧‍👦", "Traditional",
                 "The {honoree} Family Reunion",
                 "Family: where life begins and love never ends",
                 "Feel-good folk / nostalgic pop", 0.95,
                 "Together is our favourite place to be."),
    EventProfile("Travel Memories", "✈️", "Modern",
                 "{title}",
                 "Not all who wander are lost",
                 "Cinematic travel / world music", 0.85,
                 "Travel is the only thing you buy that makes you richer."),
    EventProfile("Festivals", "🪔", "Traditional",
                 "{title}",
                 "May the festive lights shine on you all year",
                 "Festive traditional / celebratory", 0.9,
                 "Celebrations are the language of the heart."),
    EventProfile("Retirement", "🌅", "Classic",
                 "Happy Retirement, {honoree}",
                 "The best chapter starts now",
                 "Reflective piano / smooth jazz", 1.15,
                 "Retirement: when every day is a weekend."),
    EventProfile("Farewell", "👋", "Minimal",
                 "Farewell, {honoree}",
                 "Goodbyes are only until we meet again",
                 "Emotional acoustic / soft piano", 1.1,
                 "How lucky we are to have something that makes goodbye hard."),
    EventProfile("Memorial Tribute", "🕊️", "Vintage",
                 "In Loving Memory of {honoree}",
                 "Forever in our hearts",
                 "Gentle piano / ambient strings", 1.35,
                 "Those we love never truly leave us."),
    EventProfile("Custom Event", "✨", "Modern",
                 "{title}",
                 "Thank you for being part of our story",
                 "Your choice", 1.0,
                 "Every moment is a memory in the making."),
]}


def get_event(name: str) -> EventProfile:
    """Look up an event profile; unknown names fall back to Custom Event."""
    return EVENTS.get(name, EVENTS["Custom Event"])


def resolve_text(template: str, title: str, honoree: str) -> str:
    """Fill {title}/{honoree} placeholders, degrading gracefully when empty."""
    text = template.replace("{honoree}", honoree or title or "You")
    text = text.replace("{title}", title or honoree or "Our Memories")
    return text
