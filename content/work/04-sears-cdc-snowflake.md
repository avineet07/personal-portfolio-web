---
id: sears-cdc-snowflake
order: 4
title: "High-Throughput AWS DMS CDC to Snowflake Streaming Engine"
company: "Sears Holdings"
role: "Senior Technical Associate"
period: "May 2024 – Present"
location: "Hyderabad, India"
category: "Data Engineering"
summary: "Replaced slow legacy batch ETL with real-time Change Data Capture (CDC) streaming into S3 and Snowpipe, reducing query times by 2-3x and cutting cloud warehouse spend by 40%."
metrics:
  - "2x–3x Query Speedup"
  - "-40% Warehouse Spend"
  - "Sub-Minute Latency"
techStack:
  - AWS DMS
  - Amazon S3
  - Snowflake (Streams/Tasks)
  - Snowpipe
  - SQL
  - CDC
media:
  type: image
  src: /src/assets/snowflake-cdc-flow.svg
  alt: "AWS DMS CDC to Snowflake Streaming Engine"
related:
  - aws-smart-proxy
  - sears-agentic-workflow
---

<h3>Executive Summary</h3>
<p>Legacy batch ETL tools (Matillion) periodically queried our production operational databases with heavy SQL scans, inducing database locks and introducing multi-hour data latency. At Sears Holdings, I spearheaded the migration to an event-driven <strong>Change Data Capture (CDC)</strong> streaming pipeline using <strong>AWS Database Migration Service (DMS)</strong>, <strong>Amazon S3</strong>, and <strong>Snowpipe</strong>.</p>

<figure class="media-figure">
  <img lightbox src="/src/assets/snowflake-cdc-flow.svg" alt="Streaming Architecture from Source DBs to Snowflake" class="media-image" />
  <figcaption class="media-caption">Architecture Diagram: Zero-Polling CDC Engine -> S3 Micro-Batches -> Snowpipe -> SCD2 Tables.</figcaption>
</figure>

<h3>1. Architecture & Engineering Decisions</h3>
<ul>
  <li><strong>Zero-Polling Replication:</strong> AWS DMS reads database transaction logs (WAL/Oplogs) directly without touching database query engines, eliminating CPU spikes on transactional services.</li>
  <li><strong>Micro-Batching to S3:</strong> DMS flushes changes in micro-batched Parquet files to an S3 staging bucket.</li>
  <li><strong>Automated Snowpipe Ingestion:</strong> S3 event notifications trigger Snowpipe, continuously ingesting records into landing tables within seconds of occurrence.</li>
  <li><strong>Stream & Task Merges (SCD Type 2):</strong> Snowflake Streams track new insertions and deletions, while scheduled Tasks execute high-performance MERGE operations to maintain historical dimensions.</li>
  <li><strong>MongoDB NoSQL Extraction:</strong> Engineered Python ETL pipelines extracting unstructured data from MongoDB NoSQL databases into refined relational models.</li>
</ul>

<h3>2. Measurable Outcomes</h3>
<ul>
  <li><strong>Query Latency:</strong> Dashboard query response times improved by <strong>2x to 3x</strong> due to indexing, clustering, and pre-clustered SCD2 tables.</li>
  <li><strong>Cloud Spend Reduction:</strong> Decreased Snowflake compute consumption by <strong>40%</strong> by eliminating full table re-scans.</li>
  <li><strong>Data Freshness:</strong> Reduced operational data lag from 6 hours to <strong>under 60 seconds</strong>.</li>
</ul>
