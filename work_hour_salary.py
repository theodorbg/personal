from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterable, Optional, Sequence

import pandas as pd


HOURLY_RATE = 185.0   # Timeløn før skat
AM_BIDRAG = 0.08      # AM-bidrag, 8 %
A_SKAT = 0.37         # A-skat, justér efter din sats


@dataclass
class WorkDay:
    """En arbejdsdag uden behov for en rigtig kalenderdato."""

    dag: int
    moedetid: Optional[time]
    gaetid: Optional[time]
    frokost_minutter: float
    note: str = ""

    @property
    def timer(self) -> float:
        if self.moedetid is None or self.gaetid is None:
            return 0.0

        # Vi bruger en vilkårlig fælles dato, fordi vi kun skal beregne varighed.
        basisdato = datetime(2000, 1, 1).date()

        start = datetime.combine(basisdato, self.moedetid)
        slut = datetime.combine(basisdato, self.gaetid)

        # Håndterer arbejde over midnat
        if slut < start:
            slut += timedelta(days=1)

        arbejdstid = slut - start - timedelta(minutes=self.frokost_minutter)
        return max(arbejdstid.total_seconds() / 3600, 0.0)


class Month:
    """
    En lønperiode fra d. 22 til d. 22.

    Dag 22-31 tolkes som første del af perioden.
    Dag 1-21 tolkes som anden del af perioden.

    `year` bruges kun som label i oversigten og Excel-eksporten.
    """

    def __init__(
        self,
        year: int,
        month: str,
        WorkDays: Iterable[Sequence] = (),
        print_oversigt: bool = True,
    ):
        self.year = year
        self.month = month
        self.dage: list[WorkDay] = []

        for day in WorkDays:
            self._tilføj_fra_tuple(day)

        self.dage.sort(key=lambda dag: (dag.dag >= 22, dag.dag))

        if print_oversigt:
            self.print_oversigt()

    def _tilføj_fra_tuple(self, day: Sequence) -> None:
        if len(day) not in (4, 5):
            raise ValueError(
                "Hver WorkDay skal være [dag, mødtid, gåtid, frokost] "
                "eller [dag, mødtid, gåtid, frokost, note]."
            )

        dag, moedetid, gaetid, frokost, *rest = day
        note = rest[0] if rest else ""

        if not 1 <= dag <= 31:
            raise ValueError(f"Ugyldig dag: {dag}")

        self.dage.append(
            WorkDay(
                dag=dag,
                moedetid=self._til_tid(moedetid),
                gaetid=self._til_tid(gaetid),
                frokost_minutter=float(frokost),
                note=str(note),
            )
        )

    @staticmethod
    def _til_tid(value: int | str | time | None) -> Optional[time]:
        if value is None:
            return None

        if isinstance(value, time):
            return value

        if isinstance(value, int):
            value = f"{value:04d}"

        return datetime.strptime(value, "%H%M").time()

    @property
    def samlede_timer(self) -> float:
        return sum(dag.timer for dag in self.dage)

    @property
    def bruttoløn(self) -> float:
        return self.samlede_timer * HOURLY_RATE

    @property
    def am_bidrag(self) -> float:
        return self.bruttoløn * AM_BIDRAG

    @property
    def a_skat(self) -> float:
        skattepligtig = self.bruttoløn * (1 - AM_BIDRAG)
        return skattepligtig * A_SKAT

    @property
    def udbetaling(self) -> float:
        return self.bruttoløn - self.am_bidrag - self.a_skat

    def til_dataframe(self) -> pd.DataFrame:
        rækker = []

        for dag in self.dage:
            brutto = dag.timer * HOURLY_RATE
            netto = brutto * (1 - AM_BIDRAG) * (1 - A_SKAT)

            rækker.append(
                {
                    "Dag": dag.dag,
                    "Mødt": dag.moedetid,
                    "Gået": dag.gaetid,
                    "Frokost (min)": dag.frokost_minutter,
                    "Timer": round(dag.timer, 2),
                    "Note": dag.note,
                    "Løn før skat": round(brutto, 2),
                    "Overslag udbetaling": round(netto, 2),
                }
            )

        return pd.DataFrame(rækker)

    def print_oversigt(self) -> None:
        print(f"\nÅr: {self.year}")
        print(f"Month: {self.month}")
        print(f"\nArbejdsdage: {len(self.dage)}")
        print(f"Timer: {self.samlede_timer:.1f}")
        print(f"Avg. timer pr dag: {self.samlede_timer / len(self.dage):.1f}")
        print(f"Avg. timer pr uge: {self.samlede_timer / (30.5/7.0):.1f}")
        print(f"\nBruttoløn: {self.bruttoløn:.0f} kr.")
        # print(f"AM-bidrag: {self.am_bidrag:.2f} kr.")
        # print(f"A-skat: {self.a_skat:.2f} kr.")
        print(f"Overslag udbetaling: {self.udbetaling:.0f} kr.\n")

    def gem_til_excel(self, filnavn: str) -> None:
        detaljer = self.til_dataframe()

        oversigt = pd.DataFrame(
            [
                {
                    "År": self.year,
                    "Samlede timer": round(self.samlede_timer, 2),
                    "Bruttoløn": round(self.bruttoløn, 2),
                    "AM-bidrag": round(self.am_bidrag, 2),
                    "A-skat": round(self.a_skat, 2),
                    "Overslag udbetaling": round(self.udbetaling, 2),
                }
            ]
        )

        with pd.ExcelWriter(filnavn, engine="openpyxl") as writer:
            detaljer.to_excel(writer, sheet_name="Timer", index=False)
            oversigt.to_excel(writer, sheet_name="Oversigt", index=False)


# September – oktober 2026
sep_okt = Month(
    year=2026,
    month="September – oktober",
    WorkDays=(
        [28, 1000, 1920, 30],
        [29, 1530, 1715, 0, "arbejde juni"],
        [1, 900, 1835, 30],
        [5, 920, 1700, 0],
        [6, 900, 1655, 0],
        [8, 845, 1610, 30],
        [12, 935, 1830, 30],
        [13, 820, 1620, 0],
        [14, 940, 1730, 0],
        [19, 930, 1735, 0]
    )
)

okt_nov = Month(
    year=2026,
    month="Oktober – november",
    WorkDays=(
        [2, 1100, 1130, 0],
        [3, 1030, 2110, 0],
        [5, 1005, 1845, 0],
        [6, 900, 1730, 0],
        [7, 1000, 1530, 0]
    )
)