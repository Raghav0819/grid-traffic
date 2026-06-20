"""
Motor Vehicles Act 1988 (as amended by MV Amendment Act 2019) —
Hand-crafted legal corpus for Chapter XIII (Sections 177-210).

Sections relevant to two-wheeler violations are fully reproduced.
Other sections are summarised with key penalty amounts.
Source: indiacode.nic.in + MV Amendment Act 2019 gazette.

Structure: a list of dicts, each representing one legal section.
  section     : section number string  e.g. "194D"
  title       : short title
  full_text   : complete legal text of that section
  violation   : internal violation key  (matches config.MV_ACT keys)
  fine_inr    : primary fine amount (int)
  imprisonment: imprisonment provision if any (str or None)
  disqualification: licence disqualification (str or None)
  compoundable: bool — can be compounded by officer on spot
  keywords    : list of retrieval keywords
"""

CORPUS = [

    {
        "section": "128",
        "title": "Safety measures for motor cycle drivers and pillion riders",
        "full_text": (
            "Section 128 — Safety measures for motor cycle drivers and pillion riders.\n"
            "No driver of a motor cycle shall carry more than one person in addition to himself "
            "on the motor cycle, and no person shall be so carried otherwise than sitting on a "
            "proper seat securely fixed to the motor cycle behind the driver's seat with his "
            "feet resting on foot rests fixed to the motor cycle. "
            "Every person driving or riding on a motor cycle including the pillion rider shall "
            "wear a protective headgear conforming to the standards of Bureau of Indian "
            "Standards (BIS)."
        ),
        "violation": None,
        "fine_inr": None,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": False,
        "keywords": ["pillion", "motorcycle rider", "safety measures", "number of riders",
                     "triple riding", "two wheeler capacity", "section 128"],
    },

    {
        "section": "129",
        "title": "Wearing of protective headgear",
        "full_text": (
            "Section 129 — Wearing of protective headgear.\n"
            "Every person above the age of 4 years driving or riding or being carried on a "
            "motorcycle shall wear protective headgear (helmet) conforming to the standards "
            "of Bureau of Indian Standards (BIS), while in a public place. "
            "The helmet must be properly fastened with a strap provided for the purpose. "
            "Exception: Sikhs wearing a turban are exempt from this provision."
        ),
        "violation": None,
        "fine_inr": None,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": False,
        "keywords": ["helmet", "headgear", "protective headgear", "BIS helmet",
                     "motorcycle helmet", "pillion helmet", "section 129"],
    },

    {
        "section": "177",
        "title": "General provision for punishment of offences",
        "full_text": (
            "Section 177 — General provision for punishment of offences.\n"
            "Whoever contravenes any provision of this Act or of any rule, regulation or "
            "notification made thereunder shall, if no penalty is provided for the "
            "contravention, be punishable for the first offence with a fine which may "
            "extend to five hundred rupees, and for any subsequent offence with a fine "
            "which may extend to one thousand five hundred rupees. "
            "(As amended by MV Amendment Act 2019 — first offence ₹500, subsequent ₹1500)"
        ),
        "violation": None,
        "fine_inr": 500,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["general penalty", "traffic violation", "fine", "contravention",
                     "section 177"],
    },

    {
        "section": "181",
        "title": "Driving vehicles in contravention of Section 3 or Section 4",
        "full_text": (
            "Section 181 — Driving vehicles in contravention of Section 3 or Section 4.\n"
            "Whoever drives a motor vehicle in contravention of any condition of a driving "
            "licence or in contravention of the provisions of Section 3 (necessity for "
            "driving licence) or Section 4 (age limit for drivers) shall be punishable "
            "with a fine of five thousand rupees. "
            "(As amended by MV Amendment Act 2019 — ₹5,000)"
        ),
        "violation": None,
        "fine_inr": 5000,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["driving without licence", "no licence", "driving licence",
                     "unlicensed driver", "section 181"],
    },

    {
        "section": "183",
        "title": "Driving at excessive speed",
        "full_text": (
            "Section 183 — Driving at excessive speed.\n"
            "(1) Whoever drives a motor vehicle in contravention of the speed limits "
            "referred to in Section 112 shall be punishable: "
            "for light motor vehicle — fine of ₹1,000 for first offence, ₹2,000 for "
            "subsequent offence; "
            "for medium or heavy vehicle — fine of ₹2,000 for first offence, ₹4,000 for "
            "subsequent offence. "
            "(As amended by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 1000,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["speeding", "over speed", "excessive speed", "speed limit", "section 183"],
    },

    {
        "section": "184",
        "title": "Driving dangerously",
        "full_text": (
            "Section 184 — Driving dangerously.\n"
            "Whoever drives a motor vehicle at a speed or in a manner which is dangerous "
            "to the public, having regard to all the circumstances of the case including "
            "the nature, condition and use of the place where the vehicle is driven, and "
            "the amount of traffic which actually is at the time or which might reasonably "
            "be expected to be at the time, shall be punishable: "
            "for first offence — imprisonment up to 6 months or fine of ₹5,000 or both; "
            "for subsequent offence — imprisonment up to 2 years or fine of ₹10,000 or both."
        ),
        "violation": None,
        "fine_inr": 5000,
        "imprisonment": "First offence: up to 6 months. Subsequent: up to 2 years.",
        "disqualification": None,
        "compoundable": False,
        "keywords": ["dangerous driving", "reckless driving", "section 184"],
    },

    {
        "section": "185",
        "title": "Driving by a drunken person or under influence of drugs",
        "full_text": (
            "Section 185 — Driving by a drunken person or under influence of drugs.\n"
            "Whoever drives or attempts to drive a motor vehicle in any public place while "
            "under the influence of alcohol or a drug to such an extent as to be incapable "
            "of exercising proper control over the vehicle shall be punishable: "
            "first offence — imprisonment up to 6 months or fine of ₹10,000 or both; "
            "subsequent offence — imprisonment up to 2 years or fine of ₹15,000 or both. "
            "(As amended by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 10000,
        "imprisonment": "First: up to 6 months. Subsequent: up to 2 years.",
        "disqualification": None,
        "compoundable": False,
        "keywords": ["drunk driving", "drunken driving", "alcohol", "DUI", "drugs", "section 185"],
    },

    {
        "section": "194",
        "title": "Penalty for using vehicle exceeding permissible weight",
        "full_text": (
            "Section 194 — Penalty for using vehicle exceeding permissible weight.\n"
            "(1) Whoever drives a motor vehicle or causes or allows a motor vehicle to be "
            "driven in contravention of the provisions of Section 113 (laden weight), "
            "Section 114 (axle weight) or Section 115 (light motor vehicle weight) "
            "shall be punishable with fine of ₹20,000 and an additional ₹2,000 per "
            "tonne of excess load, together with the liability to unload the excess."
        ),
        "violation": None,
        "fine_inr": 20000,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["overloading", "permissible weight", "laden weight", "axle weight",
                     "section 194"],
    },

    {
        "section": "194A",
        "title": "Carriage of excess passengers",
        "full_text": (
            "Section 194A — Carriage of excess passengers.\n"
            "Whoever drives a motor vehicle or causes or allows a motor vehicle to be "
            "driven with more passengers than the permitted capacity shall be punishable "
            "with a fine of ₹200 per excess passenger. "
            "(As introduced by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 200,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["excess passengers", "overcrowding", "vehicle capacity", "section 194A"],
    },

    {
        "section": "194B",
        "title": "Penalty for not wearing seat belt",
        "full_text": (
            "Section 194B — Penalty for not wearing seat belt / child restraint.\n"
            "(1) Whoever drives a motor vehicle or causes or allows a motor vehicle to be "
            "driven without the driver or the co-passenger wearing a seat belt or child "
            "restraint system as required under Section 138(4) shall be punishable with "
            "a fine of one thousand rupees. "
            "(2) Whoever causes or allows a child below 14 years to be seated in the "
            "front seat of a motor vehicle shall be punishable with a fine of ₹1,000. "
            "(As introduced by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 1000,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["seat belt", "seatbelt", "child restraint", "front seat child",
                     "section 194B"],
    },

    # ══════════════════════════════════════════════════════════════════════
    # PRIMARY SECTIONS — directly relevant to our detected violations
    # ══════════════════════════════════════════════════════════════════════

    {
        "section": "194C",
        "title": "Penalty for violation of safety measures for motorcycle drivers and pillion riders",
        "full_text": (
            "Section 194C — Penalty for violation of safety measures for motor cycle "
            "drivers and pillion riders (Motor Vehicles Amendment Act 2019).\n"
            "Whoever drives a motor cycle or causes or allows a motor cycle to be driven "
            "in contravention of the provisions of Section 128 or the rules or regulations "
            "made thereunder shall be punishable with a fine of one thousand rupees and "
            "he shall be disqualified for holding a driving licence for a period of "
            "three months.\n"
            "Section 128 limits two-wheeler occupancy to driver + one pillion rider. "
            "Carrying two or more pillion riders (triple riding or more) is a direct "
            "contravention of Section 128 and attracts penalty under this section.\n"
            "This is a compoundable offence — the challan can be paid on the spot to "
            "the authorised officer."
        ),
        "violation": "triple_riding",
        "fine_inr": 1000,
        "imprisonment": None,
        "disqualification": "3 months disqualification from holding driving licence",
        "compoundable": True,
        "keywords": ["triple riding", "tripling", "three riders", "pillion", "extra rider",
                     "more than one pillion", "section 194C", "section 128", "two wheeler limit",
                     "motorcycle capacity", "safety measures motorcycle"],
    },

    {
        "section": "194D",
        "title": "Penalty for not wearing helmet",
        "full_text": (
            "Section 194D — Penalty for not wearing protective headgear / helmet "
            "(Motor Vehicles Amendment Act 2019).\n"
            "Whoever drives a motor cycle or causes or allows a motor cycle to be driven "
            "in contravention of the provisions of Section 129 or the rules or regulations "
            "made thereunder shall be punishable with a fine of one thousand rupees and "
            "he shall be disqualified for holding a driving licence for a period of "
            "three months.\n"
            "Section 129 mandates that every person above 4 years of age driving or riding "
            "or being carried on a motorcycle shall wear a BIS-compliant protective "
            "headgear properly fastened. This applies to both the driver and pillion rider. "
            "Exception: Sikhs wearing a turban are exempt.\n"
            "This is a compoundable offence — the challan can be paid on the spot to "
            "the authorised officer.\n"
            "Prior to the 2019 amendment the fine was ₹100; it was enhanced to ₹1,000 "
            "to improve road safety compliance and reduce head-injury fatalities."
        ),
        "violation": "no_helmet",
        "fine_inr": 1000,
        "imprisonment": None,
        "disqualification": "3 months disqualification from holding driving licence",
        "compoundable": True,
        "keywords": ["no helmet", "without helmet", "no headgear", "helmet not worn",
                     "riding without helmet", "pillion without helmet",
                     "section 194D", "section 129", "protective headgear", "BIS helmet",
                     "helmet fine", "helmet violation", "no-helmet"],
    },

    {
        "section": "194E",
        "title": "Failure to give way to emergency vehicles",
        "full_text": (
            "Section 194E — Failure to give free passage to emergency vehicles.\n"
            "Whoever while driving a motor vehicle fails to draw to the side of the road "
            "on the approach of a fire service vehicle, ambulance, or other emergency "
            "vehicle as specified by the State Government shall be punishable with "
            "imprisonment for a term which may extend to six months, or with a fine "
            "of ten thousand rupees or with both. "
            "(As introduced by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 10000,
        "imprisonment": "Up to 6 months",
        "disqualification": None,
        "compoundable": False,
        "keywords": ["ambulance", "emergency vehicle", "fire service", "give way",
                     "section 194E"],
    },

    {
        "section": "196",
        "title": "Driving uninsured vehicles",
        "full_text": (
            "Section 196 — Driving uninsured vehicles.\n"
            "Whoever drives a motor vehicle or causes or allows a motor vehicle to be "
            "driven in contravention of the provisions of Section 146 (compulsory "
            "third-party insurance) shall be punishable: "
            "first offence — fine of ₹2,000 or imprisonment up to 3 months or both; "
            "subsequent offence — fine of ₹4,000 or imprisonment up to 3 months or both. "
            "(As amended by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 2000,
        "imprisonment": "Up to 3 months",
        "disqualification": None,
        "compoundable": True,
        "keywords": ["no insurance", "uninsured vehicle", "insurance", "third party",
                     "section 196", "section 146"],
    },

    {
        "section": "201",
        "title": "Penalty for causing obstruction to free flow of traffic",
        "full_text": (
            "Section 201 — Penalty for causing obstruction to free flow of traffic.\n"
            "(1) Whoever keeps a disabled vehicle on any public place in such a manner "
            "as to cause impediment to the free flow of traffic shall be liable for "
            "penalty of ₹500 per hour for a two-wheeler or light motor vehicle, and "
            "₹1,000 per hour for medium or heavy motor vehicles, in addition to paying "
            "the towing charges. "
            "(As amended by MV Amendment Act 2019)"
        ),
        "violation": None,
        "fine_inr": 500,
        "imprisonment": None,
        "disqualification": None,
        "compoundable": True,
        "keywords": ["obstruction", "blocking traffic", "disabled vehicle", "illegal parking",
                     "towing", "section 201", "free flow of traffic"],
    },
]