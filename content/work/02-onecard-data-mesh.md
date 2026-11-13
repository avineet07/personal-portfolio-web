---
id: onecard-data-mesh
order: 2
title: "Decentralized Data Mesh & Self-Serve Analytics Platform"
company: "OneCard"
role: "Data Scientist and Data Product Manager"
period: "Jan 2021 – May 2024"
location: "Pune, India"
category: "Data Architecture"
summary: "Designed a domain-oriented data mesh across Risk, Marketing, and Operations squads, decoupling centralized bottlenecks and empowering teams to build end-to-end data products."
metrics:
  - "+30% Feature Adoption"
  - "17% → 19% Net Yield Lift"
  - "100+ Data Products"
techStack:
  - Snowflake
  - DBT
  - Apache Superset
  - AWS S3
  - Data Mesh
  - SQL
media:
  type: image
  src: /src/assets/data-mesh-arch.svg
  alt: "OneCard Enterprise Data Mesh Architecture"
related:
  - onecard-churn-engine
  - sears-cdc-snowflake
---

<h3>Executive Summary</h3>
<p>As OneCard grew to millions of transacting cardholders, our centralized data team became a bottleneck for product managers, credit analysts, and marketing operations. I led the architectural transition from a centralized monolithic warehouse to a <strong>decentralized Data Mesh</strong>, treating <em>data as a product</em> and establishing self-serve analytics across all functional business units.</p>

<figure class="media-figure">
  <img lightbox src="/src/assets/data-mesh-arch.svg" alt="OneCard Data Mesh Platform Architecture" class="media-image" />
  <figcaption class="media-caption">Architecture Diagram: Domain Data Ownership, Federated Governance, and Self-Serve Platform Backbone.</figcaption>
</figure>

<h3>1. The Bottleneck: Monolithic Data Engineering</h3>
<p>Previously, all raw event streams (swipes, payments, EMI conversions) flowed into a monolithic warehouse maintained by a single data engineering team. This created critical challenges:</p>
<ul>
  <li><strong>Lack of Domain Context:</strong> Central engineers lacked business context on credit risk underwriting nuances.</li>
  <li><strong>Slow Delivery Cycles:</strong> Product squads waited 2–4 weeks for custom SQL transformations and dashboard modifications.</li>
  <li><strong>Schema Fragility:</strong> Upstream app updates frequently broke downstream financial reconciliation pipelines.</li>
</ul>

<h3>2. The Four Pillars of Our Data Mesh Implementation</h3>
<ol>
  <li><strong>Domain-Oriented Ownership:</strong> We reorganized data ownership along business boundaries: Risk Squad owns credit underwriting tables; Marketing Squad owns engagement logs; Operations owns settlement tables.</li>
  <li><strong>Data as a Product:</strong> Every dataset was packaged with automated schema contracts, documentation, SLA guarantees, and versioned APIs.</li>
  <li><strong>Self-Serve Platform:</strong> We standardized on Snowflake, DBT, and Apache Superset, providing domain squads with declarative templates to build their own pipelines without infrastructure overhead.</li>
  <li><strong>Federated Governance:</strong> Global standards for PII tokenization, data retention, and auditing enforced automatically via CI/CD linting.</li>
</ol>

<h3>3. Realized Data Product: Net Interest Yield Optimization</h3>
<p>Under this new architecture, the Growth squad built a dynamic <em>Interest Yield Data Product</em>. By joining real-time transaction streams with tier pricing models, the team conducted agile pricing experiments that lifted OneCard's net interest yield from <strong>17% to 19%</strong>.</p>

<h3>4. Key Business Results</h3>
<ul>
  <li><strong>Adoption Lift:</strong> Non-technical product managers and analysts increased active feature usage by <strong>30%</strong>.</li>
  <li><strong>Pipeline Autonomy:</strong> Reduced average time-to-insight for new analytics initiatives from 14 days to under 24 hours.</li>
  <li><strong>Audit Compliance:</strong> 100% adherence to financial compliance through automated DBT test suites and schema contracts.</li>
</ul>
