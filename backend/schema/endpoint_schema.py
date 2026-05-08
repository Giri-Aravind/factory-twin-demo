simulation_id = "ebdd2bef-f6d2-4665-8bca-dbd0555c1a3f"

endpoint_data = {
    "demandByFulfillmentDonut": {
    "display_name": "Total Aggregate Demand",
    "category": "Demand Planning",
    "chart_type": "donut",
    "query": (
        "query DonutDemandByFulfillment("
        "$simulation: UUID!, "
        "$sites: [UUID!]!, "
        "$from: Instant!, "
        "$until: Instant!, "
        "$onTimeDeliveryBuffer: Float!, "
        "$useProjectedCompletion: Boolean"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "demandByFulfillmentDonut("
        "from: $from, "
        "until: $until, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer, "
        "useProjectedCompletion: $useProjectedCompletion"
        ") { "
        "startDate "
        "stackDataList { name quantity value } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "useProjectedCompletion": False,
    },

    "user_variables": {
        "from": {
            "type": "Instant!",
            "required": True,
            "default_value": "2026-02-26T03:25:00.748Z",
            "needs_lookup": False,
            "description": "Start date for the demand data range.",
        },
        "until": {
            "type": "Instant!",
            "required": True,
            "default_value": "2027-08-26T02:25:00.748Z",
            "needs_lookup": False,
            "description": "End date for the demand data range.",
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
    },

    "response_path": ["simulation", "charts", "demandByFulfillmentDonut"]
    },
    "demandByFulfillmentHistogram": {
    "display_name": "Monthly Aggregate Demand",
    "category": "Demand Planning",
    "chart_type": "stacked_bar",
    "query": (
        "query HistogramDemandByFulfillment("
        "$simulation: UUID!, "
        "$periodBoundaries: [Instant!]!, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!, "
        "$useProjectedCompletion: Boolean"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "demandByFulfillmentHistogram("
        "periodBoundaries: $periodBoundaries, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer, "
        "useProjectedCompletion: $useProjectedCompletion"
        ") { "
        "startDate "
        "stackDataList { name quantity value } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "useProjectedCompletion": False,
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z",
                "2025-03-01T00:00:00Z", "2025-04-01T00:00:00Z",
                "2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z",
                "2025-07-01T00:00:00Z", "2025-08-01T00:00:00Z",
                "2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z",
                "2025-11-01T00:00:00Z", "2025-12-01T00:00:00Z",
                "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z",
                "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z",
                "2026-05-01T00:00:00Z", "2026-06-01T00:00:00Z",
                "2026-07-01T00:00:00Z",
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps for the histogram. Default is "
                "the full 18-month simulation window (Jan 2025 through Jul 2026)."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
    },

    "response_path": ["simulation", "charts", "demandByFulfillmentHistogram"],
    },
    "monthlyDemandByCategory": {
    "display_name": "Monthly Demand by Category",
    "category": "Demand Planning",
    "chart_type": "stacked_bar",
    "query": (
        "query DemandByCategory("
        "$simulation: UUID!, "
        "$stackType: LineItemStackInput!, "
        "$partGroupCategory: UUID, "
        "$filters: LineItemFilter!, "
        "$periodBoundaries: [Instant!]!, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!, "
        "$useProjectedCompletion: Boolean!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "monthlyDemandByCategory("
        "stackType: $stackType, "
        "partGroupCategory: $partGroupCategory, "
        "filters: $filters, "
        "periodBoundaries: $periodBoundaries, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer, "
        "useProjectedCompletion: $useProjectedCompletion"
        ") { "
        "startDate "
        "stackDataList { name quantity value } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "useProjectedCompletion": False,
        "partGroupCategory": None,
        "filters": {
            "lineItem": None,
            "fulfillmentStatus": None,
            "customer": None,
            "salesOrder": None,
            "part": None,
            "partGroupIntersection": [],
        },
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z",
                "2025-03-01T00:00:00Z", "2025-04-01T00:00:00Z",
                "2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z",
                "2025-07-01T00:00:00Z", "2025-08-01T00:00:00Z",
                "2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z",
                "2025-11-01T00:00:00Z", "2025-12-01T00:00:00Z",
                "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z",
                "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z",
                "2026-05-01T00:00:00Z", "2026-06-01T00:00:00Z",
                "2026-07-01T00:00:00Z",
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps. Default is the full 18-month "
                "simulation window (Jan 2025 through Jul 2026)."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "stackType": {
            "type": "LineItemStackInput!",
            "required": True,
            "default_value": "ORDER_TYPE",
            "needs_lookup": False,
            "allowed_values": [
                "CUSTOMER", "LINE_ITEM", "ORDER_TYPE", "PART",
                "SALES_ORDER", "SITE", "NO_STACK",
            ],
            "description": "How to break down each monthly bar. Defaults to ORDER_TYPE.",
        },
    },

    "response_path": ["simulation", "charts", "monthlyDemandByCategory"],
    },
    "categoryDemandPareto": {
    "display_name": "Demand Drill-down for Time Period",
    "category": "Demand Planning",
    "chart_type": "horizontal_bar",
    "query": (
        "query CategoryDemandPareto("
        "$simulation: UUID!, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!, "
        "$filters: LineItemFilter!, "
        "$from: Instant!, "
        "$stackType: LineItemStackInput!, "
        "$until: Instant!, "
        "$useProjectedCompletion: Boolean!, "
        "$partGroupCategory: UUID"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "categoryDemandPareto("
        "from: $from, "
        "until: $until, "
        "sites: $sites, "
        "partGroupCategory: $partGroupCategory, "
        "filters: $filters, "
        "stackType: $stackType, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer, "
        "useProjectedCompletion: $useProjectedCompletion"
        ") { "
        "part "
        "stackData { name quantity value } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "useProjectedCompletion": False,
        "partGroupCategory": None,
        "filters": {
            "lineItem": None,
            "fulfillmentStatus": None,
            "customer": None,
            "salesOrder": None,
            "part": None,
            "partGroupIntersection": [],
        },
    },

    "user_variables": {
        "from": {
            "type": "Instant!",
            "required": True,
            "default_value": "2025-01-01T00:00:00Z",
            "needs_lookup": False,
            "description": "Start date for the demand range. Defaults to simulation start.",
        },
        "until": {
            "type": "Instant!",
            "required": True,
            "default_value": "2026-07-01T00:00:00Z",
            "needs_lookup": False,
            "description": "End date for the demand range. Defaults to simulation end.",
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "stackType": {
            "type": "LineItemStackInput!",
            "required": True,
            "default_value": "ORDER_TYPE",
            "needs_lookup": False,
            "allowed_values": [
                "CUSTOMER", "LINE_ITEM", "ORDER_TYPE", "PART",
                "SALES_ORDER", "SITE", "NO_STACK",
            ],
            "description": "How to break down each part's demand. Defaults to ORDER_TYPE.",
        },
    },

    "response_path": ["simulation", "charts", "categoryDemandPareto"],
    },
    "materialShortageAnalysis": {
    "display_name": "Material Shortage Analysis",
    "category": "Supply Planning",
    "chart_type": "combo_bar_line",
    "query": (
        "query MaterialShortage("
        "$simulation: UUID!, "
        "$sites: [UUID!]!, "
        "$periodBoundaries: [Instant!]!, "
        "$selectedMaterial: UUID!, "
        "$onTimeDeliveryBuffer: Float!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "materialShortageAnalysis("
        "sites: $sites, "
        "periodBoundaries: $periodBoundaries, "
        "selectedMaterial: $selectedMaterial, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer"
        ") { "
        "overduePurchaseOrderQuantity "
        "quantityFromInventory "
        "purchaseOrderQuantity "
        "demandQuantity "
        "inventoryValue "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2026-02-05T00:43:06.239Z","2026-03-01T06:00:00.000Z",
                "2026-04-01T05:00:00.000Z","2026-05-01T05:00:00.000Z",
                "2026-06-01T05:00:00.000Z","2026-07-01T05:00:00.000Z",
                "2026-08-01T05:00:00.000Z","2026-09-01T05:00:00.000Z",
                "2026-10-01T05:00:00.000Z","2026-11-01T05:00:00.000Z",
                "2026-12-01T06:00:00.000Z","2027-01-01T06:00:00.000Z",
                "2027-02-01T06:00:00.000Z","2027-03-01T06:00:00.000Z",
                "2027-04-01T05:00:00.000Z","2027-05-01T05:00:00.000Z",
                "2027-06-01T05:00:00.000Z","2027-07-01T05:00:00.000Z",
                "2027-08-01T05:00:00.000Z","2027-09-01T04:59:59.999Z"
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps for the shortage chart. Default is "
                "the full 18-month simulation window (Jan 2025 through Jul 2026)."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "selectedMaterial": {
            "type": "UUID!",
            "required": True,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "part",
            "return_as": "single",
            "description": (
                "The part to analyze for shortage. Required — there is no "
                "sensible default. If the user does not specify a part, the "
                "extractor must signal this in missing_required."
            ),
        },
    },

    "response_path": ["simulation", "charts", "materialShortageAnalysis"],
    },
    "suppliedMaterialDemandBySupplier": {
    "display_name": "Material Demand Profile by Supplier",
    "category": "Supply Planning",
    "chart_type": "stacked_bar",
    "query": (
        "query SuppliedMaterialDemandBySupplier("
        "$simulation: UUID!, "
        "$periodBoundaries: [Instant!]!, "
        "$partSupplier: UUID, "
        "$stackType: SuppliedMaterialDemandStackType!, "
        "$partGroupCategory: UUID, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "suppliedMaterialDemandBySupplier("
        "periodBoundaries: $periodBoundaries, "
        "partSupplier: $partSupplier, "
        "stackType: $stackType, "
        "partGroupCategory: $partGroupCategory, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer"
        ") { "
        "startDate "
        "stacks { name quantity } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "partGroupCategory": None,
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z",
                "2025-03-01T00:00:00Z", "2025-04-01T00:00:00Z",
                "2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z",
                "2025-07-01T00:00:00Z", "2025-08-01T00:00:00Z",
                "2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z",
                "2025-11-01T00:00:00Z", "2025-12-01T00:00:00Z",
                "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z",
                "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z",
                "2026-05-01T00:00:00Z", "2026-06-01T00:00:00Z",
                "2026-07-01T00:00:00Z",
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps. Default is the full 18-month "
                "simulation window."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "stackType": {
            "type": "SuppliedMaterialDemandStackType!",
            "required": True,
            "default_value": "MATERIAL_SUPPLIED",
            "needs_lookup": False,
            "allowed_values": [
                "FINISHED_GOOD", "MATERIAL_SUPPLIED", "LINE_ITEM",
                "JOB", "CUSTOMER", "ORDER_TYPE",
            ],
            "description": (
                "How to break down each supplier's bar. Defaults to "
                "MATERIAL_SUPPLIED."
            ),
        },
        "partSupplier": {
            "type": "UUID",
            "required": False,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "companysite",
            "return_as": "single",
            "description": (
                "Optional. Restrict the chart to a single supplier. If the user "
                "names a supplier, emit a lookup. Otherwise omit; the GraphQL "
                "backend treats null as 'all suppliers'."
            ),
        },
    },

    "response_path": ["simulation", "charts", "suppliedMaterialDemandBySupplier"],
    },
    "suppliedMaterialDemandByMaterial": {
    "display_name": "Material Demand Profile by Material",
    "category": "Supply Planning",
    "chart_type": "stacked_bar",
    "query": (
        "query SuppliedMaterialDemandByMaterial("
        "$simulation: UUID!, "
        "$periodBoundaries: [Instant!]!, "
        "$part: UUID, "
        "$stackType: SuppliedMaterialDemandStackType!, "
        "$partGroupCategory: UUID, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "suppliedMaterialDemandByMaterial("
        "periodBoundaries: $periodBoundaries, "
        "part: $part, "
        "stackType: $stackType, "
        "partGroupCategory: $partGroupCategory, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer"
        ") { "
        "startDate "
        "stacks { name quantity } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "partGroupCategory": None,
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z",
                "2025-03-01T00:00:00Z", "2025-04-01T00:00:00Z",
                "2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z",
                "2025-07-01T00:00:00Z", "2025-08-01T00:00:00Z",
                "2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z",
                "2025-11-01T00:00:00Z", "2025-12-01T00:00:00Z",
                "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z",
                "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z",
                "2026-05-01T00:00:00Z", "2026-06-01T00:00:00Z",
                "2026-07-01T00:00:00Z",
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps. Default is the full 18-month "
                "simulation window."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "stackType": {
            "type": "SuppliedMaterialDemandStackType!",
            "required": True,
            "default_value": "MATERIAL_SUPPLIED",
            "needs_lookup": False,
            "allowed_values": [
                "FINISHED_GOOD", "MATERIAL_SUPPLIED", "LINE_ITEM",
                "JOB", "CUSTOMER", "ORDER_TYPE",
            ],
            "description": (
                "How to break down each material's bar. Defaults to "
                "MATERIAL_SUPPLIED."
            ),
        },
        "part": {
            "type": "UUID",
            "required": False,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "part",
            "return_as": "single",
            "description": (
                "Optional. Restrict the chart to a single part. If the user "
                "names a part, emit a lookup. Otherwise omit; the GraphQL "
                "backend treats null as 'all parts'."
            ),
        },
    },

    "response_path": ["simulation", "charts", "suppliedMaterialDemandByMaterial"],
    },
    "ospPartDemand": {
    "display_name": "OSP Part Demand",
    "category": "Supply Planning",
    "chart_type": "stacked_bar",
    "query": (
        "query OspPartDemand("
        "$simulation: UUID!, "
        "$periodBoundaries: [Instant!]!, "
        "$partSupplier: UUID, "
        "$part: UUID, "
        "$process: UUID, "
        "$stackType: OspPartDemandStackType!, "
        "$partGroupCategory: UUID, "
        "$sites: [UUID!]!, "
        "$onTimeDeliveryBuffer: Float!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "ospPartDemand("
        "periodBoundaries: $periodBoundaries, "
        "partSupplier: $partSupplier, "
        "part: $part, "
        "process: $process, "
        "stackType: $stackType, "
        "partGroupCategory: $partGroupCategory, "
        "sites: $sites, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer"
        ") { "
        "startDate "
        "stacks { name quantity } "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "partGroupCategory": None,
    },

    "user_variables": {
        "periodBoundaries": {
            "type": "[Instant!]!",
            "required": True,
            "default_value": [
                "2026-02-05T00:43:06.239Z","2026-03-01T06:00:00.000Z",
                "2026-04-01T05:00:00.000Z","2026-05-01T05:00:00.000Z",
                "2026-06-01T05:00:00.000Z","2026-07-01T05:00:00.000Z",
                "2026-08-01T05:00:00.000Z","2026-09-01T05:00:00.000Z",
                "2026-10-01T05:00:00.000Z","2026-11-01T05:00:00.000Z",
                "2026-12-01T06:00:00.000Z","2027-01-01T06:00:00.000Z",
                "2027-02-01T06:00:00.000Z","2027-03-01T06:00:00.000Z",
                "2027-04-01T05:00:00.000Z","2027-05-01T05:00:00.000Z",
                "2027-06-01T05:00:00.000Z","2027-07-01T05:00:00.000Z",
                "2027-08-01T05:00:00.000Z","2027-09-01T04:59:59.999Z"
            ],
            "needs_lookup": False,
            "description": (
                "Monthly boundary timestamps. Default is the full 18-month "
                "simulation window."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "stackType": {
            "type": "OspPartDemandStackType!",
            "required": True,
            "default_value": "OSP_PART",
            "needs_lookup": False,
            "allowed_values": [
                "FINISHED_GOOD", "OSP_PART", "PROCESS", "LINE_ITEM",
                "CUSTOMER", "ORDER_TYPE",
            ],
            "description": (
                "How to break down each bar. Defaults to OSP_PART."
            ),
        },
        "partSupplier": {
            "type": "UUID",
            "required": False,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "companysite",
            "return_as": "single",
            "description": (
                "Optional. Restrict the chart to a single supplier."
            ),
        },
        "part": {
            "type": "UUID",
            "required": False,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "part",
            "return_as": "single",
            "description": (
                "Optional. Restrict the chart to a single OSP part."
            ),
        },
        "process": {
            "type": "UUID",
            "required": False,
            "default_value": None,
            "needs_lookup": True,
            "lookup_table": "process",
            "return_as": "single",
            "description": (
                "Optional. Restrict the chart to a single outsourced process "
                "(e.g. machining, heat treating, plating)."
            ),
        },
    },

    "response_path": ["simulation", "charts", "ospPartDemand"],
    },
    "buyerActions": {
    "display_name": "Long Lead Time Purchase Order Placement Alerts",
    "category": "Supply Planning",
    "chart_type": "table",
    "query": (
        "query BuyerActions("
        "$simulation: UUID!, "
        "$sites: [UUID!]!, "
        "$from: Instant, "
        "$until: Instant, "
        "$maybeMinDuration: Int, "
        "$leadTimeType: leadTimeType!, "
        "$defaultScheduler: scheduleType!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "buyerActions("
        "sites: $sites, "
        "from: $from, "
        "until: $until, "
        "maybeMinDuration: $maybeMinDuration, "
        "leadTimeType: $leadTimeType, "
        "defaultScheduler: $defaultScheduler"
        ") { "
        "purchasedPart "
        "purchasedPartIdentifier "
        "supplier "
        "purchasedLeadTime "
        "earliestTargetArrival "
        "earliestPlacement "
        "totalDemanded "
        "quantityToPurchase "
        "estimatedPrice "
        "associatedLineItems { "
        "salesOrder lineItem due finishedPart customer "
        "targetArrival placement quantity "
        "} "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
    },

    "user_variables": {
        "from": {
            "type": "Instant",
            "required": True,
            "default_value": "2025-01-01T00:00:00Z",
            "needs_lookup": False,
            "description": "Start date for demand calculation. Defaults to simulation start.",
        },
        "until": {
            "type": "Instant",
            "required": True,
            "default_value": "2026-07-01T00:00:00Z",
            "needs_lookup": False,
            "description": "End date for demand calculation. Defaults to simulation end.",
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
        "leadTimeType": {
            "type": "leadTimeType!",
            "required": True,
            "default_value": "DEMONSTRATED",
            "needs_lookup": False,
            "allowed_values": ["DEMONSTRATED", "SYSTEM"],
            "description": (
                "How lead time is calculated. DEMONSTRATED uses observed past "
                "performance. SYSTEM uses configured static lead times. "
                "Defaults to DEMONSTRATED."
            ),
        },
        "defaultScheduler": {
            "type": "scheduleType!",
            "required": True,
            "default_value": "STANDARD",
            "needs_lookup": False,
            "allowed_values": [
                "STANDARD", "MACHINE", "UNCONSTRAINED", "NO_SCHEDULE",
            ],
            "description": (
                "Which scheduler to use for this calculation. Defaults to STANDARD."
            ),
        },
        "maybeMinDuration": {
            "type": "Int",
            "required": False,
            "default_value": None,
            "needs_lookup": False,
            "description": (
                "Optional minimum lead time in days. Only purchase orders with "
                "total lead time >= this value will appear. Omit if user does "
                "not mention a numeric threshold."
            ),
        },
    },

    "response_path": ["simulation", "charts", "buyerActions"],
    },
    "NewPartIntroductionDemandTable": {
    "display_name": "New Part Introduction Demand Table",
    "category": "Demand Planning",
    "chart_type": "table",
    "query": (
        "query NewPartIntroductionDemandTable("
        "$simulation: UUID!, "
        "$determiningDate: Instant!, "
        "$filters: LineItemFilter!, "
        "$onTimeDeliveryBuffer: Float!, "
        "$from: Instant, "
        "$until: Instant, "
        "$sites: [UUID!]!, "
        "$useProjectedCompletion: Boolean!, "
        "$partGroupCategoryName: String!"
        ") { "
        "simulation(identifier: $simulation) { "
        "charts { "
        "NewPartIntroductionDemandTable("
        "determiningDate: $determiningDate, "
        "filters: $filters, "
        "onTimeDeliveryBuffer: $onTimeDeliveryBuffer, "
        "from: $from, "
        "until: $until, "
        "sites: $sites, "
        "useProjectedCompletion: $useProjectedCompletion, "
        "partGroupCategoryName: $partGroupCategoryName"
        ") { "
        "part "
        "description "
        "faiDate "
        "lastProductionDate "
        "inventoryQuantity "
        "partGroupList "
        "orders { "
        "lineItem customer due quantity value "
        "} "
        "} "
        "} "
        "} "
        "}"
    ),

    "fixed_variables": {
        "simulation": simulation_id,
        "onTimeDeliveryBuffer": 0.0,
        "useProjectedCompletion": False,
        "filters": {"partGroupIntersection": []},
    },

    "user_variables": {
        "partGroupCategoryName": {
            "type": "String!",
            "required": True,
            "default_value": "Platform",
            "needs_lookup": False,
            "allowed_values": ["Platform", "Customer", "Part Family"],
            "description": (
                "Which part group category to organize NPI parts by. The user "
                "may say 'by platform', 'by customer', or 'by part family'. "
                "Defaults to Platform."
            ),
        },
        "determiningDate": {
            "type": "Instant!",
            "required": True,
            "default_value": "2024-01-01T00:00:00Z",
            "needs_lookup": False,
            "description": (
                "Cutoff date for NPI status. Parts not produced since this "
                "date are flagged as new. Defaults to 12 months before "
                "simulation start."
            ),
        },
        "from": {
            "type": "Instant",
            "required": False,
            "default_value": None,
            "needs_lookup": False,
            "description": (
                "Optional start date for the demand window. Omit when user "
                "does not mention a start date."
            ),
        },
        "until": {
            "type": "Instant",
            "required": False,
            "default_value": None,
            "needs_lookup": False,
            "description": (
                "Optional end date for the demand window. Omit when user "
                "does not mention an end date."
            ),
        },
        "sites": {
            "type": "[UUID!]!",
            "required": True,
            "default_value": [],
            "needs_lookup": True,
            "lookup_table": "site",
            "return_as": "list",
            "description": "List of site UUIDs. Empty list means all sites.",
        },
    },

    "response_path": ["simulation", "charts", "NewPartIntroductionDemandTable"],
    }
}


# ---------------------------------------------------------------------------
# Compatibility helpers
# ---------------------------------------------------------------------------
# Other parts of the pipeline (endpoint_selector, populate_vector_db, tests)
# expect a `get_endpoint_by_name` accessor that returns the endpoint dict
# with `endpoint_name` set on it. Keep that contract so we don't have to
# change every consumer.

def get_endpoint_by_name(name):
    """Return the endpoint dict for `name`, with endpoint_name attached.

    Returns None if the name is not in endpoint_data.
    """
    spec = endpoint_data.get(name)
    if spec is None:
        return None
    # Shallow merge: endpoint_name is the dict key in endpoint_data,
    # but downstream consumers read it as a field on the dict.
    return {**spec, "endpoint_name": name}


# Sequence used by populate_vector_db.py for consistency checks.
ENDPOINT_NAMES = list(endpoint_data.keys())