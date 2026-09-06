## A. Executive conclusion (аудиторский вердикт)

Прикреплённый отчёт  в целом методологически корректен, добросовестно разделяет measured evidence и Sepia-эвристику, и его центральные фактические утверждения проверяются напрямую по репозиторию. Прямая сверка с `narrative-pass.md`, `discourse-pass.md`, `professional-pass.md`  подтверждает точность цифр (QUDsim move-frequency ~19% vs ~0.2–0.3%, Nonaka & Perry network density 0.18 vs 0.34–0.47, recontextualization depth 3.28 vs 2.95) и корректность различения "Sepia heuristic" vs "measured result" vs "vendor guidance", уже выполненного в оригинальном отчёте. Аудит не нашёл искажений первоисточников, но выявил зоны, которые в приложенном документе не были доведены до операциональной глубины, требуемой заданием (пп. 20–23): сравнение с классическим NLP-стеком (SRL/AMR/OpenIE/PDTB/RST/QUD-parsing) и полный JSON Schema draft для AMOS.[^1]

**Usefulness for AMOS: 6/10.** Sepia — не источник semantic ground truth, а каталог relation-vocabulary и эвристик распознавания дискурсивных паттернов, откалиброванных на детекции AI-текста, а не на построении онтологий.
**Fork: NO.** Гипотеза AIMETON подтверждается — ни один механизм Sepia не требует форка; всё нужное — идеи, а не код.
**Integrate directly: NO.** Прямая интеграция Sepia-правил в AMOS создаёт риск смешения calibration-эвристик (AI-detection) с evidence-семантикой (AMOS provenance).
**Harvest ideas: YES**, преимущественно из раздела 8 (QUD/discourse) и раздела 6 (temporal/recontextualization) — но с обязательным re-grounding на первичные статьи (QUDsim, StoryScope, Nonaka & Perry), а не на Sepia-пересказ.
**Primary target layer: E1→E2 boundary (discourse-move / implicit-question tagging) и O/A candidate-projection слой** — не E0 raw evidence.

***

## B. Верификация ключевых фактических утверждений отчёта

Ниже — построчная сверка самых нагруженных claim'ов приложенного исследования с первичными файлами репозитория, полученными напрямую из GitHub (не из README).

| Утверждение отчёта | Файл в репозитории | Результат сверки |
|---|---|---|
| QUD: "linear interview" / "reflection tail" как машинные паттерны; comparison/verification ~0.2–0.3%, consequence/procedure ~19% | `skills/sepia/references/discourse-pass.md` §1 | Подтверждено буквально, включая outline test (A) и цитату про Kafka-cop echo test  |
| Temporal: recontextualization depth 3.28(human)/2.95(AI); anachrony intensity 2.58/2.31; revelation pacing "back-loaded" как human fingerprint | `narrative-pass.md` §4 | Подтверждено точно, включая различение "staging information" (discourse_time вводится явно через "hold back the cause, open with the effect")  |
| Social/actor graph: network density 0.18 vs 0.34–0.47 (Nonaka & Perry), affect −0.06 vs +0.24…+0.66, антагонистический clustering 0.395 vs 0.07–0.21 | `narrative-pass.md` §6 | Подтверждено точно, включая явную инструкцию "draw the cast graph with signed edges"  |
| Professional-pass: specificity/file:line/stance/verification как отдельные checks с separate weighting по document shape | `skills/sepia/references/professional-pass.md` | Подтверждено; weighting-таблица (article-like vs short-answer) и whitelist ("conventional ≠ slop") воспроизведены верно  |
| Sepia не evidence-система, prescriptions помечены как "Sepia design inferences unless cited source explicitly tested the intervention" | все три файла | Подтверждено — эта оговорка присутствует буквально в каждом файле как стандартная преамбула, что валидирует ключевой тезис отчёта о дисциплине разделения evidence/heuristic |
| PR-история содержит настоящие architecture-review итерации (например PR #232: детектор-эвристика была удалена как category error после 4 раундов Codex-review) | `pull_request #232` | Подтверждено напрямую через GitHub API  — это усиливает аргумент отчёта о зрелости evidence-ledger практики Sepia, но также подтверждает, что сами авторы Sepia периодически откатывают собственные эвристики как ложные — сильный аргумент против прямого копирования правил без ре-валидации |

Вывод: фактическая база отчёта надёжна. Инженерная и методологическая часть (пп. C–K ниже) — зона, где аудит добавляет глубину.

***

## C. Дополнение: сопоставление с классическим NLP-стеком (закрывает п.20 задания)

Отчёт  не выполняет полноценно требование "не изобретать велосипед". Ниже — недостающая матрица.[^1]

| Направление | Что даёт Sepia нового | Что лучше взять из классики | Что лучше делать LLM | Комбинация для AMOS |
|---|---|---|---|---|
| Semantic Role Labeling (PropBank/FrameNet) | Ничего — Sepia не выполняет SRL | Готовая, проверенная predicate-argument taxonomy (agent/patient/instrument) | Zero-shot SRL LLM-промптом на входном тексте | AMOS Event-node должен использовать PropBank-роли, а не Sepia's "acts_on/participates_in" |
| OpenIE / relation extraction | Sepia даёт discourse-level relation vocabulary (contradicts, verifies, recontextualizes), которого нет в classic OpenIE | Триплет-экстракция (subject-predicate-object) с confidence scoring — зрелая, tunable | Long-range coreference resolution до OpenIE | Sepia relation-vocabulary как top-level taxonomy over OpenIE triples |
| AMR / UDS | Ничего сравнимого — Sepia не строит graph-based meaning representation | Полная, formalized meaning graph с абстракцией от syntax | Neural AMR-parsers (SPRING, AMRBART) как extractor backend | AMOS SemanticNode может напрямую наследовать AMR node/edge типизацию для event/entity слоя |
| Event extraction (ACE/ERE style) | Ничего формального; Sepia использует implicit event-typing через narrative decisions (decision/change/conflict) не как taxonomy, а как rubric-heuristic | ACE event ontology (trigger, argument roles, event types) — готовая, evaluable | Zero/few-shot event trigger detection | Sepia's decision-таксономия (theme/plot/ending) как domain-specific overlay над generic ACE events |
| Temporal relation extraction (TimeML/TempEval) | Sepia различает event_time vs discourse_time неявно через "revelation pacing", но без формализма | TimeML (BEFORE/AFTER/OVERLAP/BEGINS/ENDS/etc.) — точная, стандартизированная taxonomy | Extraction temporal expressions and anchoring | AMOS temporal layer ДОЛЖЕН базироваться на TimeML/TempEval-3, а не изобретать свою — Sepia лишь подтверждает important distinction (event_time ≠ discourse_time), не даёт формальную taxonomy |
| Causal relation extraction | Sepia различает "causal-chain continuity" (measured metric 3.92 vs 4.20) и "echo test" против narrative adjacency — полезная эвристика against false causality | CausalBank, PDTB causal relations, ROCStories causal chains — measured datasets | LLM causal-chain reconstruction с explicit uncertainty | Echo test Sepia как heuristic guard against narrative adjacency → causal collapse; formal taxonomy — из PDTB |
| Discourse parsing (RST/PDTB) | Sepia's QUD-check близок к Question-Under-Discussion parsing (Riester, Roberts), но проще; move-classification (claim/explanation/verification) частично overlaps с PDTB relation senses | RST (nucleus-satellite relations), PDTB (Comparison/Contingency/Expansion/Temporal) — зрелые annotation schemes | QUD-tree induction (Westera & Rohde, De Kuthy) | AMOS discourse_move должен маппироваться на PDTB relation senses + QUD-tree, Sepia move-list — как starting vocabulary, не final |
| Claim/evidence extraction | professional-pass даёт practical checklist (specificity, source-backed, stance) но не formal claim-evidence graph | Argument mining (claim/premise/warrant, Toulmin model), SciFact/FEVER claim verification datasets | Stance detection, claim decomposition | AMOS E1/E2 separation должен использовать argument-mining schemas, Sepia checklist — как QA heuristic layer поверх |
| GraphRAG / knowledge graph extraction | Ничего — Sepia не строит persistent knowledge graph | Actual graph construction, entity resolution, community detection | Relation extraction promptable pipeline | AMOS ContextBundle compilation прямо соответствует GraphRAG community summarization pattern |
| Ontology induction | Ничего формального | OWL/RDF-based induction, distant supervision | LLM-assisted schema induction with human-in-loop validation | AMOS O-projection должен использовать ontology-induction практики, не narrative rubric |

**Итог по направлению:** большинство "открытий" Sepia (QUD move types, causal echo test, temporal recontextualization) — это переоткрытие уже существующих идей QUD-теории Robertса/Roberts (1996/2012) и PDTB relation senses в упрощённой, calibration-специфичной форме. Ценность Sepia — не в новой теории, а в **эмпирически измеренном частотном распределении** этих move'ов в LLM-тексте против человеческого — этого нет в классических датасетах PDTB/RST, которые не сравнивают AI vs human. Это делает Sepia полезной как источник *baseline distribution priors*, а не как parsing framework.

***

## D. Дополнение: приоритизированные первоисточники (закрывает п.21)

| Sepia grain | Первоисточник | Датасет/taxonomy | Приоритет для AMOS |
|---|---|---|---|
| QUD check | Roberts (1996/2012) Questions Under Discussion; QUDsim COLM 2025 | QUDsim's move-sequence corpus (61,608 stories) | **P0** — читать QUDsim напрямую, не Sepia-дайджест |
| Discourse move classification | PDTB 3.0 sense hierarchy | PDTB annotated corpus | **P0** |
| Temporal semantics | TimeML / TempEval-3 | TimeBank corpus | **P0** |
| Causal chains / echo test | Xu et al. PNAS 2025 ("drop ratio" regeneration test); CausalBank | — | **P1** |
| Social/actor network | Nonaka & Perry 2025 | измеренный character-network dataset | **P1** |
| Recontextualization | Sepia не даёт первоисточника отдельно от StoryScope narrative-pass measurements — требует отдельного библиографического поиска в discourse-revision literature (belief revision, defeasible reasoning) | AGM belief revision theory | **P1** — этот грейн у Sepia слабее обоснован, чем остальные; в самом narrative-pass.md он присутствует как метрика ("recontextualization depth"), но не как отдельно исследованный механизм |
| Claim/evidence checklist | Argument mining (Toulmin); Slop taxonomy (Shaib et al.) | FEVER, SciFact | **P2** |
| AMR/event extraction | ACE, AMR Bank | — | **P0** (не из Sepia вовсе, но обязательно для AMOS) |

***

## E. AMOS Semantic Relation taxonomy (черновик, обоснованный исследованием)

Группы и происхождение (Sepia / research / AMOS-новое):

**Temporal** (base: TimeML, дополнено Sepia recontextualization insight): `before`, `after`, `overlaps`, `valid_during`, `observed_at`, `revealed_after` (Sepia-specific: различие discourse_time vs event_time), `recontextualized_by` (Sepia-specific, слабо обосновано первично).

**Causal** (base: PDTB Contingency, дополнено Sepia echo-test guard): `causes`, `enables`, `prevents`, `results_in`, `contributing_factor` — с обязательным полем `derivation_type: adjacency_inferred | explicitly_stated`, так как Sepia прямо показывает риск narrative-adjacency-as-causality.

**Evidential** (base: argument mining, professional-pass checklist): `supports`, `contradicts`, `verifies`, `weakens`, `qualifies`.

**Discursive** (base: PDTB + QUD, Sepia move vocabulary): `answers` (implicit_question), `explains`, `compares_with`, `summarizes`, `digresses`.

**Ontological** (base: classic KG, не из Sepia): `is_a`, `part_of`, `instance_of`, `state_of`.

**Actor** (base: social network analysis, Sepia-specific metrics as calibration priors only): `interacts_with`, `owns`, `controls`, `opposes`, `supports_person` — с явным hard rule: affect/tie sign — inferred, not verified, always `status: candidate`.

**Evolution** (Sepia-specific, требует доп. обоснования): `recontextualizes`, `invalidates`, `supersedes`, `refines` — рекомендуется трактовать как AMOS-собственную семантику (близкую к AGM belief revision), Sepia лишь подтверждает наблюдаемость феномена, не даёт формализм.

***

## F. Что НЕ переносить в AMOS (расширение п.18/I)

- Все style-pass / model-fingerprints механизмы — чисто AI-detection, language- и model-version-specific, разваливаются при смене релиза модели (сам репозиторий подтверждает это через историю PR #46, #45, где vendor fingerprints требуют постоянного пересмотра) .
- "Rarity move" эвристика (narrative-pass.md, п. "The rarity move") — художественно-специфична, неприменима к engineering-документам.
- Voice-skills / Hemingway profile — irrelevant для semantic extraction.
- Sentence-rhythm dispersion checks (§5 style-pass) — orthogonal к semantics, языко-зависимы.
- Chinese calibration (references/languages/zh.md) — полезна как *методологический пример* локализации, но не как контент для русской калибровки.

***

## G. Дополнение по русскому языку (закрывает п.17 глубже)

Language-independent (можно переносить без изменений): causal-chain distinctions, temporal ordering distinctions (event_time vs discourse_time), QUD move categories (claim/explanation/comparison/verification), evidence/claim separation — это семантические, не синтаксические категории.

Зависящие от английского синтаксиса и НЕ переносимые: sentence-length dispersion thresholds, punctuation density signals, nominalization/passive-voice heuristics (в русском морфология отличается кардинально — падежная система, свободный порядок слов делают style-pass §2–3 неприменимыми без полной пересборки).

Требующие отдельной калибровки: русский discourse-connector inventory (аналог zh.md для 连词), т.к. русский язык имеет собственную плотность союзов и вводных конструкций, для которых нет измеренного бейзлайна ни в Sepia, ни в HC3-подобном корпусе.

***

## H. Скорректированный roadmap (P0/P1/P2)

**P0 (можно проверить сейчас):** извлечь QUD/discourse-move vocabulary как top-level taxonomy для TextBlock.discourse_move; связать с PDTB relation senses напрямую, минуя Sepia-пересказ; построить temporal event_time/discourse_time разделение по TimeML на GitHub Issues/PR-корпусе пользователя (aerospace/GNSS-репозитории — хороший тестовый домен).

**P1 (после MVP semantic relation layer):** causal echo-test как hallucination-guard в extractor; actor-graph generalization (Person/Agent/Team/Repository) с обязательным confidence/status полем; recontextualization semantics — оформить через AGM belief revision, а не Sepia-метрику.

**P2 (advanced research):** cross-document relation quality benchmark; QUD-tree induction (Westera/Rohde) как research track; ontology induction pipeline для O-projection.

***

## Заключение аудита

Прикреплённый документ  — качественная, фактически точная работа, полностью соответствующая заданной методологии (evidence-boundary discipline, разделение measured/heuristic/vendor). Аудит **не выявил ложных или искажённых утверждений** при прямой сверке с репозиторием . Главное дополнение аудита — систематическое позиционирование grain'ов Sepia относительно зрелого NLP-стека (раздел C) и уточнение, что самый слабо обоснованный (но самый ценный для AMOS) грейн — "recontextualization" — у самой Sepia не имеет отдельного первоисточника и должен разрабатываться AMOS-командой самостоятельно, вероятно на основе теории belief revision, а не путём копирования Sepia-метрики "recontextualization depth".[^1]

Итоговый вариант ответа согласно категориям задания (п.25): **B+E** — Sepia содержит несколько ценных зёрен (в первую очередь QUD/discourse move vocabulary и temporal/causal distinguishing heuristics), но первичные исследования (QUDsim, PDTB, TimeML, Nonaka & Perry) существенно ценнее самой Sepia, и оптимальная архитектура AMOS — комбинация классического NLP-formalism (AMR/PDTB/TimeML/PropBank) с LLM-based extraction, откалиброванная Sepia-подобными empirical move-frequency priors, но не наследующая её код или rubric напрямую.

---

## References

1. [AMOS_Semantic_Relation_Layer_Sepia_Research_ru.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/5702513/6e09e8fc-3a93-4d00-b04d-72a8c0e28182/AMOS_Semantic_Relation_Layer_Sepia_Research_ru.md) - AIMETON Memory OS AMOS Nanako0129sepia, commit d8a0f948cc46a0ba0d610df7458c4e8943bfe51a, 2026-09-05 ...

