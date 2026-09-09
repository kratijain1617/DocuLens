"""Canonical text for the five demonstration PDFs.

The PDF generator and the labeled evaluation set both read this module,
so page numbers and quotations stay aligned.
"""

SAMPLE_DOCUMENTS = [
    {
        "file_name": "Apartment Rental Agreement.pdf",
        "title": "Apartment Rental Agreement",
        "category": "Rental agreement",
        "pages": [
            {
                "blocks": [
                    {
                        "section": "Parties and Premises",
                        "paragraphs": [
                            "This Apartment Rental Agreement is entered into between Harbor and Pine Properties LLC, the landlord, and Jordan Ellis, the tenant.",
                            "The premises are Apartment 4B at 418 Cedar Street, Portland, Oregon.",
                            "The apartment is a one-bedroom unit for residential use only.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Lease Term",
                        "paragraphs": [
                            "The lease begins on September 1, 2026 and expires on August 31, 2027.",
                            "The tenant may renew only by signing a written renewal at least thirty days before the expiration date.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Monthly Rent",
                        "paragraphs": [
                            "The monthly rent is $1,850 and is due on the first day of each month.",
                            "The rent payment deadline is the first day of each month.",
                            "A late fee of $75 applies if rent is received after the fifth day of the month.",
                        ],
                    },
                    {
                        "section": "Security Deposit",
                        "paragraphs": [
                            "The security deposit shall be equal to one month's rent.",
                            "The landlord may apply the security deposit to unpaid rent or damage beyond ordinary wear.",
                            "The remaining deposit shall be returned within 31 days after the tenant moves out.",
                        ],
                    },
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Early Termination",
                        "paragraphs": [
                            "If the tenant ends the lease early, the tenant must give sixty days of written notice and pay a fee equal to one month's rent.",
                            "The early termination fee does not apply if the tenant is called to active military duty.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Utilities and Maintenance",
                        "paragraphs": [
                            "The tenant shall pay electricity, gas, and internet service.",
                            "The landlord shall maintain the roof, exterior walls, and building plumbing.",
                            "The tenant must report leaks within 48 hours of discovering them.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Pets",
                        "paragraphs": [
                            "A pet deposit of $300 is required before any approved pet moves in.",
                            "Approved pets incur an additional pet rent of $25 per month.",
                            "Aggressive dog breeds listed in Exhibit B are not permitted.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "House Rules",
                        "paragraphs": [
                            "Quiet hours are from 10:00 p.m. to 7:00 a.m. every day.",
                            "Guests may stay no more than fourteen consecutive nights without written landlord consent.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Governing Law",
                        "paragraphs": [
                            "Ordinary wear means minor scuffs that do not affect the structure or appliances.",
                            "This agreement is governed by the laws of the State of Oregon.",
                            "Notices must be sent by email and certified mail to the addresses in this agreement.",
                        ],
                    }
                ]
            },
        ],
    },
    {
        "file_name": "University Student Policy Manual.pdf",
        "title": "University Student Policy Manual",
        "category": "University document",
        "pages": [
            {
                "blocks": [
                    {
                        "section": "Introduction",
                        "paragraphs": [
                            "This University Student Policy Manual applies to all enrolled undergraduate and graduate students for the 2026-2027 academic year.",
                            "Students are responsible for reading catalog rules before registering for courses.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Course Withdrawal",
                        "paragraphs": [
                            "The course withdrawal deadline is Friday of the eighth week of the term, October 24, 2026.",
                            "A withdrawal submitted by this deadline appears as a W on the transcript and does not affect the grade point average.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Registrar Deadline Notice",
                        "paragraphs": [
                            "The Office of the Registrar lists the course withdrawal deadline as October 17, 2026.",
                            "Students who rely on this notice should confirm the date with the academic calendar before submitting a form.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Attendance Requirements",
                        "paragraphs": [
                            "The attendance requirement is that students must attend at least 80 percent of scheduled class meetings to remain in good standing.",
                            "Instructors may drop a student who misses more than two laboratories without notice.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Required Documents",
                        "paragraphs": [
                            "Required documents for enrollment are a government-issued photo identification, an official transcript, and an immunization record.",
                            "International students must also provide a valid passport and a current I-20.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Tuition Refunds",
                        "paragraphs": [
                            "A full tuition refund is available when a student withdraws before the end of the first week of the term.",
                            "Withdrawals in the second week receive a 50 percent tuition refund.",
                            "No tuition refund is issued after the second week.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Academic Standing",
                        "paragraphs": [
                            "A student is placed on academic probation when the cumulative GPA falls below 2.00.",
                            "Students on probation must meet with an advisor before registering for the next term.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Appeals",
                        "paragraphs": [
                            "A student may appeal a withdrawal decision within ten business days by filing a written petition with the Academic Standards Committee.",
                        ],
                    }
                ]
            },
        ],
    },
    {
        "file_name": "Technical Product Manual.pdf",
        "title": "Technical Product Manual",
        "category": "Technical manual",
        "pages": [
            {
                "blocks": [
                    {
                        "section": "Product Overview",
                        "paragraphs": [
                            "The Northstar Field Analyzer NX-400 measures soil moisture, conductivity, and temperature in the field.",
                            "Read this technical manual completely before installing or operating the analyzer.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Safety Warnings",
                        "paragraphs": [
                            "Disconnect the battery before opening the sensor housing.",
                            "Do not immerse the display unit in water, because the enclosure is splash resistant but not waterproof.",
                            "Wear eye protection when replacing the probe tip.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Installation",
                        "paragraphs": [
                            "To install the product, charge the battery for four hours, attach the probe hand-tight, and run the on-screen calibration with the supplied reference block.",
                            "Mount the analyzer upright on the tripod plate before connecting external probes.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Operation",
                        "paragraphs": [
                            "Press the silver power button for two seconds until the status light turns green.",
                            "Select a measurement profile before inserting the probe into soil.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Troubleshooting",
                        "paragraphs": [
                            "Error E-17 means the probe is not detected.",
                            "To troubleshoot error E-17, reseat the connector, clean the contacts with a dry cloth, and restart the analyzer.",
                            "If error E-17 remains, replace the probe cable listed as part NX-CBL-2.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Maintenance",
                        "paragraphs": [
                            "Calibrate the analyzer every 90 days or after any firmware update.",
                            "Store the unit between 0 and 40 degrees Celsius.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Specifications",
                        "paragraphs": [
                            "The NX-400 weighs 1.4 kilograms and operates for up to 12 hours on a full charge.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Warranty",
                        "paragraphs": [
                            "The warranty period is two years from the purchase date for manufacturing defects.",
                            "The warranty does not cover damage from immersion or unauthorized modification.",
                        ],
                    }
                ]
            },
        ],
    },
    {
        "file_name": "Research Paper.pdf",
        "title": "Research Paper",
        "category": "Research paper",
        "pages": [
            {
                "blocks": [
                    {
                        "section": "Abstract",
                        "paragraphs": [
                            "This paper studies whether showing page-level citations reduces unsupported answers in document question answering.",
                            "We evaluate 120 questions across rental agreements, university policies, and technical manuals.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Research Question",
                        "paragraphs": [
                            "The main research question is whether citation-constrained answering lowers the rate of unsupported claims compared with unconstrained generation.",
                            "A secondary question asks whether readers trust an answer more when the cited passage is highlighted.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Methodology",
                        "paragraphs": [
                            "The methodology used a retrieval pipeline that split each document into page-level passages, ranked them with term frequency, and required the model to quote a retrieved passage.",
                            "Three reviewers labeled every answer as supported, partially supported, conflicting, or not found.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Main Findings",
                        "paragraphs": [
                            "The main findings show that citation-constrained answers reduced unsupported claims from 18 percent to 4 percent.",
                            "Readers located the supporting passage 2.3 times faster when the cited page was opened automatically.",
                            "Accuracy was highest on rental agreements and lowest on documents that contained conflicting dates.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Results by Document Type",
                        "paragraphs": [
                            "On rental agreements the system answered 92 percent of factual questions with the correct page.",
                            "On university policies the correct-page rate was 81 percent because two official dates conflicted.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Limitations",
                        "paragraphs": [
                            "The limitations are that the study includes only English PDFs of fewer than 200 pages and does not measure scanned documents with poor text layers.",
                            "The reviewer pool was small, with only three annotators, so label agreement may not generalize.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Discussion",
                        "paragraphs": [
                            "The authors conclude that evidence should be shown beside every material claim, especially when a document contains more than one deadline.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "References",
                        "paragraphs": [
                            "This demonstration paper does not cite external publications.",
                            "The labeled questions were written for the DocuLens evaluation set.",
                        ],
                    }
                ]
            },
        ],
    },
    {
        "file_name": "Employee Handbook.pdf",
        "title": "Employee Handbook",
        "category": "Policy or handbook",
        "pages": [
            {
                "blocks": [
                    {
                        "section": "Welcome",
                        "paragraphs": [
                            "This employee handbook applies to all regular employees of Lumen Field Instruments.",
                            "The handbook is not an employment contract and does not change at-will employment.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Employment Status",
                        "paragraphs": [
                            "New employees complete a 90-day introductory period before becoming eligible for remote-work privileges.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Paid Time Off",
                        "paragraphs": [
                            "Full-time employees accrue 15 days of paid time off per calendar year.",
                            "Unused paid time off up to five days may carry into the next year.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Benefits",
                        "paragraphs": [
                            "Lumen Field Instruments matches employee 401(k) contributions up to 4 percent of eligible pay.",
                            "Medical, dental, and vision coverage begins on the first day of the month after the start date.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Remote Work",
                        "paragraphs": [
                            "Employees who have completed the introductory period may work remotely up to three days each week.",
                            "During the first 90 days, new hires must work on site at least four days each week.",
                            "The on-site attendance requirement for new hires is four days each week during the introductory period.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Workplace Conduct",
                        "paragraphs": [
                            "Employees must report safety hazards to a manager before the end of the shift.",
                            "Harassment, including repeated unwelcome remarks, is prohibited.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Separation",
                        "paragraphs": [
                            "Employees who resign are asked to give at least two weeks of written notice.",
                            "Accrued unused paid time off is paid on the final paycheck.",
                        ],
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "section": "Acknowledgement",
                        "paragraphs": [
                            "Employees acknowledge that they have received this handbook and will ask Human Resources about any policy they do not understand.",
                        ],
                    }
                ]
            },
        ],
    },
]


def page_count(document: dict) -> int:
    return len(document["pages"])
