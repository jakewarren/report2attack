# ATT&CK Mapping Report

**Source:** https://www.sentinelone.com/labs/contagious-interview-threat-actors-scout-cyber-intel-platforms-reveal-plans-and-ops/
**Title:** Contagious Interview | North Korean Threat Actors Reveal Plans and Ops by Abusing Cyber Intel Platforms
**Generated:** 2026-01-19 18:28:28 UTC
**LLM Provider:** openai-gpt-5-nano

## Summary

- **Total Techniques:** 20
- **High Confidence (≥0.8):** 17
- **Medium Confidence (0.5-0.8):** 3
- **Tactics Covered:** 8

## Table of Contents

- [Command And Control](#Command and Control)
- [Execution](#Execution)
- [Initial Access](#Initial Access)
- [Resource Development](#Resource Development)
- [Collection](#collection)
- [Defense Evasion](#defense-evasion)
- [Reconnaissance](#reconnaissance)
- [Resource Development](#resource-development)

---

## Command And Control {#Command and Control}

### T1665: Hide Infrastructure

**Confidence:** █████████░ (0.90)

**Evidence:**
> Some may have been voluntarily deactivated by the threat actors themselves, likely to avoid seizure or further investigation, particularly if the domains were linked to their operational security

### T1105: Ingress Tool Transfer

**Confidence:** ████████░░ (0.85)

**Evidence:**
> "method of interaction with the server, such as the use of the curl command" | "Malware download initiations are logged in files such as client_ips_start.json and client_ips_mac_start.json , which capture operating system–specific payload delivery."

---

## Execution {#Execution}

### T1204.004: Malicious Copy and Paste

**Confidence:** █████████░ (0.92)

**Evidence:**
> they are then instructed to copy and paste command lines, often involving utilities like curl , to download and execute a supposed update from a separate malware distribution server, unknowingly deploying malware in the process.

### T1204: User Execution

**Confidence:** ███████░░░ (0.75)

**Evidence:**
> to trick targets into executing malware

---

## Initial Access {#Initial Access}

### T1598.003: Spearphishing Link

**Confidence:** ████████░░ (0.85)

**Evidence:**
> A targeted job seeker receives an invitation to participate in a job application process, directing them to a lure website where they are prompted to complete a skill assessment.

---

## Resource Development {#Resource Development}

### T1583.001: Domains

**Confidence:** █████████░ (0.95)

**Evidence:**
> The attackers align with the domain quiz-nest[.]com , while Paxos corresponds to domains such as paxos-video-interview[.]com and paxosassessments[.]com . The account marvel714jm[@]gmail.com , which used the Paxos affiliation, was also used to register the domain paxos-video-interview[.]com . This suggests the actors leveraged their own infrastructure and fabricated brands to create a more convincing facade of legitimacy. | mvsolution9@gmail.com has been used to register two Contagious Interview domains: evalassesso.com, speakure.com.

### T1608.001: Upload Malware

**Confidence:** █████████░ (0.90)

**Evidence:**
> "newly deployed ClickFix malware distribution servers, such as api.camdriverhelp[.]club and api.drive-release[.]cloud, were exposing ContagiousDrop applications along with the log files they had generated"

### T1583: Acquire Infrastructure

**Confidence:** ████████░░ (0.85)

**Evidence:**
> We observed a high rate of new infrastructure deployment by the Contagious Interview threat actors alongside losses of existing infrastructure due to actions by service providers, which supports this assessment. | they rapidly deployed new infrastructure in response to service provider takedowns.

---

## Collection {#collection}

### T1213.005: Messaging Applications

**Confidence:** █████████░ (0.90)

**Evidence:**
> In addition, we identified strong indicators that the threat actors were using Slack, a messaging platform commonly used for team communication and collaboration, to coordinate their activities.

---

## Defense Evasion {#defense-evasion}

### T1036.010: Masquerade Account Name

**Confidence:** █████████░ (0.92)

**Evidence:**
> The threat actors used a diverse range of names, from generic handles like jimmr to pop-culture references such as Rock Lee (a character from the Japanese anime series Santiago Montes). The reuse of the name Anika Larkin for two different accounts, invite[@]quiz-nest[.]com and mvsolution9[@]gmail.com, combined with both accounts being registered from the same IP address (181.215.9[.]29 ) within approximately two minutes, suggests the involvement of a single individual.

---

## Reconnaissance {#reconnaissance}

### T1589.002: Email Addresses

**Confidence:** █████████░ (0.92)

**Evidence:**
> We present below the email addresses used for Validin account registrations, along with the date, time, and originating IP addresses of these registrations. | For example, marvel714jm[@]gmail.com and jimmr6587[@]gmail.com have been used to register the paxos-video-interview[.]com and skill-share[.]org domains, respectively. | The email addresses used for account registrations as well as the IP addresses from which the registrations were conducted.

### T1681: Search Threat Vendor Data

**Confidence:** █████████░ (0.90)

**Evidence:**
> actively monitor cyber threat intelligence to detect infrastructure exposure and scout for new assets | The Contagious Interview threat actors also use VirusTotal, or monitor what information about their infrastructure and malware is available on the platform, in conjunction with Validin. | North Korean threat groups actively examine CTI information to identify threats to their operations and improve the resilience and effectiveness of their campaigns, depending on their operational priorities.

### T1597.001: Threat Intel Vendors

**Confidence:** █████████░ (0.90)

**Evidence:**
> register and use Validin community access accounts within approximately 24 hours after Validin published a blog post on 11 March 2025 | These included VirusTotal and the apt_lazarus.txt file, which is part of the Maltrail project and publicly available on GitHub. This file is regularly updated with domain names, IP addresses, and URLs attributed to the Lazarus umbrella APT cluster, as well as sources providing attribution information or context, such as social media, blog posts, and other threat intelligence platforms (including VirusTotal and Validin). VirusTotal is a malware analysis service and threat intelligence platform that aggregates detection results, reputation assessments, and contextual information for files, URLs, domains, and IP addresses from a wide range of detection engines, third-party tools, and its user community. The very first search term used by the threat actors was the keyword TalentCheck , entered on 12 March 2025 at 22:44:40 UTC. | The Contagious Interview threat actors also use VirusTotal, or monitor what information about their infrastructure and malware is available on the platform, in conjunction with Validin.

### T1589: Gather Victim Identity Information

**Confidence:** █████████░ (0.90)

**Evidence:**
> "registration forms requesting information such as full name, affiliation, and reason for registration."

### T1593: Search Open Websites/Domains

**Confidence:** ████████░░ (0.85)

**Evidence:**
> the jimmr6587[@]gmail.com account was the first to search for the domain webcamfixer[.]online on 12 March 2025 at 22:54:19 UTC

### T1589.003: Employee Names

**Confidence:** ███████░░░ (0.72)

**Evidence:**
> The threat actors used a diverse range of names, from generic handles like jimmr to pop-culture references such as Rock Lee (a character from the Japanese anime series Santiago Montes).

### T1596.002: WHOIS

**Confidence:** █████░░░░░ (0.55)

**Evidence:**
> The domain registration records for versusx.us include the email address brooksliam534@gmail.com.

---

## Resource Development {#resource-development}

### T1585: Establish Accounts

**Confidence:** █████████░ (0.92)

**Evidence:**
> The threat actors started creating Validin community accounts on 12 March 2025 at 22:44:11 UTC, an activity which spanned a relatively short interval of approximately 15 minutes, suggesting a concentrated and coordinated approach. | Some affiliations correspond to fake hiring platforms operated by Contagious Interview. For example, Quiz Nest aligns with the domain quiz-nest[.]com, while Paxos corresponds to domains such as paxos-video-interview[.]com and paxosassessments[.]com.

### T1585.002: Email Accounts

**Confidence:** ████████░░ (0.85)

**Evidence:**
> The email addresses used for Validin account registrations. | The threat actors used Google Gmail addresses that we had already been tracking as Contagious Interview artifacts at the time of registration.

### T1586.002: Email Accounts

**Confidence:** ████████░░ (0.85)

**Evidence:**
> "login attempts on 9 May 2025 using the excellentreporter321[@]gmail.com and marvel714jm[@]gmail.com accounts, which had been blocked by Validin in March 2025. The threat actors’ shift to using non-Gmail addresses, along with their continuous attempts to bypass Validin’s access controls" | notify the threat actors via email about victim engagement.

---

