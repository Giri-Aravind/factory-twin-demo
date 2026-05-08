# endpoint_catalog.py

ENDPOINT_SELECTION_TEXT = {
    "demandByFulfillmentDonut": """
Endpoint name:
demandByFulfillmentDonut

Chart / business name:
Total Aggregate Demand

Purpose:
Returns one aggregate demand snapshot for a selected time range and site.
It summarizes demand by fulfillment status such as Overdue, Forecasted, and Firm Order.
Use this when the user wants a total, high-level demand number, or current demand snapshot.

Use when user asks:
- total demand
- aggregate demand
- overall demand
- demand snapshot
- demand at a glance
- order book size
- open demand position
- order pipeline
- total order pipeline
- total firm orders
- total overdue orders
- total forecasted demand
- how many overdue orders
- how many firm orders
- how many forecasted orders
- total demand for a site
- total demand for Minneapolis
- total demand for St. Cloud
- demand summary for selected time range
- sum of demand across a date range
- demand total in dollars
- total demand value
- total demand quantity

Sample questions:
- What is the total aggregate demand?
- Show me total demand.
- Give me a demand snapshot.
- What is the total demand for Minneapolis?
- What is the aggregate demand at St. Cloud?
- How many overdue orders are there?
- What is the firm order count?
- What is the forecasted demand total?
- What is our open demand position?
- What is the total order pipeline?
- Show aggregate orders right now.
- Give me demand at a glance.
- What is the order book size?
- What is the total demand in dollars?

Do not use when:
- user asks for demand by month
- user asks for monthly trend
- user asks for demand over time
- user asks to identify the highest demand month
- user asks which month has the most demand
- user asks for peak demand month
- user asks for demand broken down by customer, part, platform, order type, or category
- user asks for top demanded parts inside a specific period
- user asks for NPI or new part demand
- user asks for material shortage
- user asks for supplier or purchased material demand
- user asks for OSP demand
- user asks for buyer action or purchase order placement alerts

Choose instead:
- demandByFulfillmentHistogram for monthly aggregate demand trends, peak demand month, or month with highest demand
- monthlyDemandByCategory for monthly demand broken down by category
- categoryDemandPareto for part-level drill-down inside a time period
- NewPartIntroductionDemandTable for NPI or new part demand
- materialShortageAnalysis for shortage analysis of a selected material
- suppliedMaterialDemandBySupplier for bought material demand by supplier
- suppliedMaterialDemandByMaterial for bought material demand by material or part
- ospPartDemand for outside processing demand
- buyerActions for purchase order placement alerts
""",

    "demandByFulfillmentHistogram": """
Endpoint name:
demandByFulfillmentHistogram

Chart / business name:
Monthly Aggregate Demand

Purpose:
Returns monthly aggregate demand over time.
It shows total demand by period or month, including quantity and dollar value.
Use this when the user wants to compare months, identify the peak demand month,
or find the month with the highest demand in dollars or quantity.
This endpoint is for monthly aggregate demand without a category breakdown.

Use when user asks:
- monthly demand
- monthly aggregate demand
- demand trend
- demand over time
- demand by month
- month over month demand
- demand forecast over time
- monthly order pipeline
- demand trend for a site
- monthly demand for Minneapolis
- monthly demand for St. Cloud
- demand for both sites by month
- identify month with most demand
- month with highest demand
- peak demand month
- maximum demand month
- highest demand month
- highest dollar demand month
- month with most demand in dollars
- month with highest demand value
- compare monthly demand values
- which month has the most demand
- which month has the highest dollar value
- aggregate demand by period
- highest monthly demand
- lowest monthly demand
- month with lowest demand
- monthly demand in dollars
- demand value by month
- demand quantity by month
- demand dollars by month
- find the best or worst demand month
- compare demand across months

Sample questions:
- Identify the month with most demand in Dollars for both sites.
- Which month has the highest demand value?
- What month has the most demand in dollars?
- Show me the peak demand month.
- Which month has maximum aggregate demand?
- Show me monthly demand.
- What is the monthly aggregate demand?
- Show demand by month.
- What is the demand trend?
- How has demand changed over time?
- Show monthly demand for Minneapolis.
- Show monthly demand for St. Cloud.
- What does demand look like over the next few months?
- Show firm and forecasted demand by month.
- Show monthly overdue orders.
- What is the month-over-month demand trend?
- Which month has the lowest demand?
- Compare demand dollars across months.
- Show demand value by month for both sites.

Do not use when:
- user asks for one total aggregate demand number
- user asks for a single demand snapshot
- user asks for total demand without monthly comparison
- user asks for demand broken down by customer, platform, order type, part, product group, or category
- user asks to split, group, segment, or break down demand by a category
- user asks for top demanded parts only for one selected period
- user asks for NPI demand
- user asks for material shortage
- user asks for supplier/material demand
- user asks for OSP demand
- user asks for purchase order placement alerts

Choose instead:
- demandByFulfillmentDonut for a single aggregate demand snapshot
- monthlyDemandByCategory when the user explicitly asks for monthly demand broken down by customer, platform, order type, part, product group, or category
- categoryDemandPareto for drill-down into parts for one selected time period
- NewPartIntroductionDemandTable for NPI demand
- materialShortageAnalysis for material shortage over time
""",

    "monthlyDemandByCategory": """
Endpoint name:
monthlyDemandByCategory

Chart / business name:
Monthly Demand by Category

Purpose:
Returns monthly demand over time broken down by a selected category.
This is useful when the user wants demand by customer, part, platform, order type,
part group category, or another stack type across months.
Only use this endpoint when the user explicitly asks for a category split, category breakdown,
grouping, segmentation, or comparison between categories.

Use when user asks:
- demand by customer
- demand by platform
- demand by part
- demand by order type
- demand by product group
- demand by category
- customer demand trend
- platform demand trend
- monthly demand by customer
- monthly demand by platform
- monthly demand by part
- monthly category demand
- category-wise demand over time
- breakdown of demand by month
- which customer contributes most demand by month
- which platform has the most demand by month
- split monthly demand by category
- grouped demand by customer
- segmented demand by platform
- demand contribution by category
- demand split by customer
- demand split by platform
- demand split by order type
- compare customers by demand
- compare platforms by demand
- compare categories by demand

Sample questions:
- Show monthly demand by customer.
- Break down demand by platform.
- Show demand by part over time.
- Which customer has the most demand?
- Show monthly demand by order type.
- Show customer-wise demand trend.
- Show platform-wise demand trend.
- Break down monthly demand by product group.
- What is the demand by category for Minneapolis?
- Show demand split by customer for each month.
- Compare demand by platform month over month.
- Which platform contributes the most demand?
- Which customer contributes the most demand?
- Show demand grouped by order type.

Do not use when:
- user asks for one total aggregate demand number
- user asks for a simple monthly trend without category split
- user only asks for monthly aggregate demand
- user asks to identify the highest demand month without asking for category breakdown
- user asks for month with most demand in dollars
- user asks for peak demand month
- user asks for maximum demand month
- user asks for highest monthly demand value
- user asks for lowest monthly demand value
- user does not mention customer, platform, order type, part, product group, category, split, grouped by, segmented by, or broken down by
- user asks for top demanded parts only for one selected period
- user asks specifically for NPI demand
- user asks for purchased material demand by supplier or material
- user asks for material shortage
- user asks for OSP demand
- user asks for buyer actions or purchase order placement alerts

Choose instead:
- demandByFulfillmentDonut for a single total demand snapshot
- demandByFulfillmentHistogram for monthly aggregate demand without category split, highest demand month, peak month, or demand value by month
- categoryDemandPareto for part-level drill-down within a selected time period
- suppliedMaterialDemandBySupplier for bought material demand grouped around suppliers
- suppliedMaterialDemandByMaterial for bought material demand grouped around materials or parts
""",

    "categoryDemandPareto": """
Endpoint name:
categoryDemandPareto

Chart / business name:
Demand Drill-down for Time Period

Purpose:
Returns part-level demand rows for a selected time period.
It is used to drill into a specific month, overdue bucket, or selected period and identify which parts are driving demand.
The result includes part names and stack data with quantity and value.
Use this when the user wants detailed underlying part-level demand for a specific time period or selected demand bar.

Use when user asks:
- drill down into demand
- show parts for this month
- top demanded parts
- demand details for a selected month
- demand drill-down for January
- demand drill-down for overdue
- which parts drive demand
- what parts make up this demand
- show demand by part for a specific period
- parts contributing to demand
- top parts in June 2026
- part-level demand for a time period
- demand Pareto
- demand breakdown for selected bar
- show the underlying parts for that demand
- top parts by demand value
- top parts by demand quantity
- parts with highest demand in a period
- demand details for selected period
- line-level or part-level demand detail

Sample questions:
- Show me the top parts for January.
- Drill down into June 2026 demand.
- Which parts are driving overdue demand?
- Show the demand details for this month.
- What parts make up the demand in Minneapolis?
- Show part-level demand for St. Cloud in June.
- What are the top demanded parts for this period?
- Drill into that monthly demand bar.
- Show demand Pareto for overdue orders.
- Which parts contribute most to demand value?
- Show the parts behind this demand.
- Which parts have the highest demand in March?

Do not use when:
- user asks for one total aggregate demand number
- user asks for monthly demand trend
- user asks to identify the month with highest demand
- user asks for monthly demand by customer/platform/category
- user asks for NPI new part demand
- user asks for material shortage of one selected material
- user asks for purchased material demand by supplier/material
- user asks for OSP demand
- user asks for buyer action alerts

Choose instead:
- demandByFulfillmentDonut for a single total demand snapshot
- demandByFulfillmentHistogram for monthly aggregate demand trend or highest demand month
- monthlyDemandByCategory for monthly category breakdown
- NewPartIntroductionDemandTable for new part introduction demand
- materialShortageAnalysis for shortage analysis of a material
""",

    "NewPartIntroductionDemandTable": """
Endpoint name:
NewPartIntroductionDemandTable

Chart / business name:
NPI Demand

Purpose:
Returns demand rows for New Part Introduction parts.
A part is considered NPI if it has not been made since the determining date.
Use this when the user asks about new parts, first-time parts, recently introduced parts,
or demand for parts with no recent production history.

Use when user asks:
- NPI demand
- new part demand
- new part introduction
- new parts
- first time parts
- parts not made recently
- parts with no production since a date
- demand for new parts
- demand for NPI parts
- new product introduction demand
- NPI table
- new part orders
- recently introduced part demand
- parts requiring first article or new production attention
- demand for parts with last production date before threshold
- parts not produced recently
- parts with no recent production history
- new item demand
- first article demand
- FAI demand
- new production demand

Sample questions:
- Show me NPI demand.
- What is the new part introduction demand?
- Which new parts have demand?
- Show demand for parts not made recently.
- Show NPI demand for Minneapolis.
- Show NPI demand for St. Cloud.
- Which NPI parts have upcoming orders?
- What new parts are in the order pipeline?
- Show first-time part demand.
- Which parts have not been produced since the determining date?
- Give me the NPI demand table.
- Show new product introduction demand.
- Which parts need first article attention?

Do not use when:
- user asks for total aggregate demand
- user asks for monthly aggregate demand trend
- user asks for normal demand by customer/platform/category
- user asks for part-level drill-down for a selected period but not specifically NPI
- user asks for material shortage
- user asks for purchased material demand by supplier or material
- user asks for OSP demand
- user asks for buyer actions or purchase order alerts

Choose instead:
- demandByFulfillmentDonut for total demand snapshot
- demandByFulfillmentHistogram for monthly aggregate demand
- monthlyDemandByCategory for monthly demand by category
- categoryDemandPareto for normal part-level demand drill-down
- materialShortageAnalysis for material shortage
""",

    "buyerActions": """
Endpoint name:
buyerActions

Chart / business name:
Long Lead Time Purchase Order Placement Alerts / Buyer Actions

Purpose:
Returns buyer action rows for purchased parts that may require purchase order placement.
It shows purchased part, supplier, lead time, earliest target arrival, earliest placement date,
total demanded, quantity to purchase, estimated price, and associated line items.
Use this when the user asks what buyers need to order, when to place purchase orders,
or which long-lead purchased parts need action.

Use when user asks:
- buyer actions
- purchase order placement alerts
- PO placement alerts
- what should buyers order
- what purchase orders need to be placed
- long lead time parts
- long lead time purchase orders
- parts needing purchase
- quantity to purchase
- when to place order
- earliest placement date
- earliest target arrival
- supplier lead time
- purchased part alerts
- procurement actions
- buying recommendations
- material buying actions
- which purchased parts need attention
- order placement timing
- PO recommendations
- purchasing recommendations
- procurement alerts
- parts to buy
- buy list
- buyer worklist
- purchasing worklist

Sample questions:
- Show me buyer actions.
- What purchase orders need to be placed?
- Which long lead time parts need action?
- Show PO placement alerts.
- What should the buyer order?
- Which purchased parts need to be bought?
- When should we place purchase orders?
- Show parts with long supplier lead times.
- Which materials need procurement action?
- Show quantity to purchase by supplier.
- What are the urgent buyer actions?
- Show purchase order placement recommendations.
- What parts should procurement buy?
- Show the buyer worklist.

Do not use when:
- user asks for total demand
- user asks for monthly demand trend
- user asks for demand by customer/platform/category
- user asks for NPI demand
- user asks for material shortage chart for one material
- user asks for bought part demand profile over time
- user asks for OSP demand
- user only asks for supplier demand profile, not buyer action alerts

Choose instead:
- materialShortageAnalysis for shortage of a selected material
- suppliedMaterialDemandBySupplier for bought part demand over time by supplier
- suppliedMaterialDemandByMaterial for bought part demand over time by material
- demandByFulfillmentDonut for total demand
- categoryDemandPareto for demand drill-down by part
""",

    "suppliedMaterialDemandBySupplier": """
Endpoint name:
suppliedMaterialDemandBySupplier

Chart / business name:
Material Demand Profile by Supplier

Purpose:
Returns bought part or supplied material demand over time, viewed by supplier.
It produces bar data by period with stacks and quantities.
Use this when the user asks about material demand connected to suppliers,
supplier workload, supplier-specific bought part demand, or purchased material demand by supplier.

Use when user asks:
- material demand by supplier
- bought part demand by supplier
- supplied material demand by supplier
- supplier demand profile
- demand for a supplier
- supplier workload
- supplier material demand over time
- purchased part demand by supplier
- which supplier has demand
- supplier-wise material demand
- monthly supplier demand
- bought material demand profile
- supplier demand trend
- material requirements by supplier
- vendor demand profile
- supplier capacity demand
- purchased material by supplier
- purchased parts by supplier
- supplier-level material demand
- demand from vendor
- demand from outside supplier

Sample questions:
- Show material demand by supplier.
- Show bought part demand by supplier.
- What is the supplier demand profile?
- Show demand for this supplier.
- Which supplier has the most material demand?
- Show monthly demand by supplier.
- What materials are demanded from suppliers?
- Show supplier-wise purchased part demand.
- What is the demand trend for this supplier?
- Show supplied material demand for Minneapolis by supplier.
- Show purchased material demand by vendor.
- Which vendor has the highest bought part demand?

Do not use when:
- user asks for material demand by selected material or part
- user asks for supplier-level demand profile but specifically for OSP or outside processing
- user asks for shortage analysis of one material
- user asks for total aggregate demand
- user asks for normal finished-good demand
- user asks for NPI demand
- user asks for OSP demand
- user asks for purchase order placement alerts or buyer actions

Choose instead:
- suppliedMaterialDemandByMaterial for bought part demand by material or selected part
- materialShortageAnalysis for shortage/inventory/PO/demand balance of one material
- buyerActions for purchase order placement alerts
- ospPartDemand for outside processing demand
- demandByFulfillmentDonut for total demand snapshot
""",

    "suppliedMaterialDemandByMaterial": """
Endpoint name:
suppliedMaterialDemandByMaterial

Chart / business name:
Material Demand Profile Drill-down / Material Demand by Material

Purpose:
Returns bought part or supplied material demand over time for a selected material or part.
It produces bar data by period with stacks and quantities.
Use this when the user wants to drill into a specific purchased material, bought part,
or component and see its demand profile over time.

Use when user asks:
- material demand by material
- bought part demand by part
- supplied material demand by part
- demand for this material
- demand for selected material
- material demand drill-down
- material demand profile drill down
- part demand profile
- bought part demand over time
- purchased component demand
- component demand trend
- demand for a specific purchased part
- monthly demand for this material
- material usage over time
- component usage over time
- selected part material demand
- purchased part profile
- bought material profile
- material requirement for selected part
- drill into selected material

Sample questions:
- Show demand for this material.
- Drill down into material demand.
- Show bought part demand by part.
- What is the demand profile for this material?
- Show monthly demand for this purchased part.
- Show supplied material demand for selected part.
- How much of this component is needed over time?
- Show material demand drill-down for Minneapolis.
- What is the demand trend for this material?
- Show the bought part demand profile.
- Show purchased component demand over time.
- Show monthly usage for this material.

Do not use when:
- user asks for material demand by supplier
- user asks for supplier-level demand profile
- user asks for shortage analysis including inventory and purchase orders
- user asks for total aggregate demand
- user asks for normal finished-good demand
- user asks for NPI demand
- user asks for OSP demand
- user asks for buyer action alerts

Choose instead:
- suppliedMaterialDemandBySupplier for bought material demand by supplier
- materialShortageAnalysis for shortage/inventory/purchase order analysis of a selected material
- buyerActions for purchase order placement recommendations
- ospPartDemand for outside processing demand
- categoryDemandPareto for finished-part demand drill-down
""",

    "materialShortageAnalysis": """
Endpoint name:
materialShortageAnalysis

Chart / business name:
Material Shortage Analysis

Purpose:
Returns shortage analysis for one selected material.
It compares demand quantity, inventory value, purchase order quantity,
overdue purchase order quantity, and current inventory quantity over time.
Use this when the user asks whether a material is short, whether inventory covers demand,
or how demand compares against incoming purchase orders and inventory.

Use when user asks:
- material shortage
- shortage analysis
- shortage for this material
- will this material run short
- inventory vs demand
- demand vs purchase orders
- demand vs inventory
- purchase order coverage
- overdue purchase orders
- current inventory quantity
- quantity from inventory
- material availability
- supply coverage
- shortage risk
- stockout risk
- inventory balance for a selected material
- demand and PO profile for a material
- do we have enough inventory
- do we have enough supply
- shortage over time
- supply gap
- demand coverage
- inventory coverage
- material supply risk

Sample questions:
- Show material shortage analysis.
- Is this material short?
- Will we run out of this material?
- Show inventory versus demand for this part.
- Show purchase orders versus demand.
- What is the shortage risk for this material?
- How much inventory do we have for this material?
- Are purchase orders enough to cover demand?
- Show overdue purchase order quantity.
- Show shortage analysis for selected material.
- Does this material have enough supply?
- Do we have enough inventory to cover demand?
- Show the supply gap for this material.

Do not use when:
- user asks for bought material demand profile only
- user asks for material demand by supplier
- user asks for material demand by material without shortage/inventory context
- user asks for total aggregate demand
- user asks for monthly demand trend
- user asks for NPI demand
- user asks for OSP demand
- user asks for buyer action alerts or recommended PO placement dates

Choose instead:
- suppliedMaterialDemandByMaterial for demand profile of a selected material
- suppliedMaterialDemandBySupplier for supplier-level material demand profile
- buyerActions for purchase order placement alerts
- demandByFulfillmentDonut for total demand
- monthlyDemandByCategory for demand breakdowns by category
""",

    "ospPartDemand": """
Endpoint name:
ospPartDemand

Chart / business name:
OSP Demand Profile

Purpose:
Returns outside processing demand over time.
It supports demand by OSP part, supplier, process, finished good, customer,
line item, order type, or part group category depending on stack type.
Use this when the user asks about outsourced processing, outside service demand,
supplier/process demand for OSP, or OSP part workload.

Use when user asks:
- OSP demand
- outside processing demand
- outsourced processing demand
- outside service demand
- OSP part demand
- demand by OSP supplier
- demand by OSP process
- outside processing workload
- supplier process demand
- OSP demand profile
- OSP demand by month
- OSP demand by process
- OSP demand by part
- OSP demand by customer
- process demand for outside processing
- outside processing supplier workload
- outsourcing demand
- subcontractor demand
- outside vendor processing demand
- external processing demand
- demand for outside vendor
- OSP workload by supplier
- OSP workload by process

Sample questions:
- Show OSP demand.
- What is the OSP demand profile?
- Show outside processing demand by month.
- Show OSP demand by supplier.
- Show OSP demand by process.
- Which OSP part has the most demand?
- Show outsourced processing workload.
- Show demand for this OSP supplier.
- Show OSP demand for this process.
- Show OSP part demand for Minneapolis.
- Break down OSP demand by customer.
- Show outside vendor processing demand.
- Which outside process has the highest demand?

Do not use when:
- user asks for normal aggregate demand
- user asks for normal monthly demand by category
- user asks for bought material demand by supplier or material
- user asks for material shortage
- user asks for purchase order placement alerts
- user asks for NPI demand
- user asks for part-level finished-good demand drill-down

Choose instead:
- suppliedMaterialDemandBySupplier for bought material demand by supplier
- suppliedMaterialDemandByMaterial for bought material demand by material
- materialShortageAnalysis for selected material shortage
- buyerActions for purchase order placement alerts
- categoryDemandPareto for normal demand drill-down by part
- monthlyDemandByCategory for normal monthly demand by category
"""
}

# Used by populate_vector_db.py to set the payload category, and by the
# endpoint selector's multi-endpoint path to fetch one Demand and one Supply
# endpoint when a query needs both buckets.
#
# IMPORTANT: when adding a new endpoint, add an entry here AND in
# ENDPOINT_SELECTION_TEXT above. populate_vector_db.py will fail loudly if
# the two dicts disagree on endpoint names.
ENDPOINT_CATEGORIES = {
    "demandByFulfillmentDonut": "Demand Planning",
    "demandByFulfillmentHistogram": "Demand Planning",
    "monthlyDemandByCategory": "Demand Planning",
    "categoryDemandPareto": "Demand Planning",
    "NewPartIntroductionDemandTable": "Demand Planning",
    "suppliedMaterialDemandBySupplier": "Supply Planning",
    "suppliedMaterialDemandByMaterial": "Supply Planning",
    "materialShortageAnalysis": "Supply Planning",
    "ospPartDemand": "Supply Planning",
    "buyerActions": "Supply Planning",
}