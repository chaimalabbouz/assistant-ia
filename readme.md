pour lancer l application :backend> uvicorn app.main:app --reload  











Voici la roadmap complète, organisée pour que ton architecture soit prête dès le départ à accueillir HR + IT + leur fusion, sans que tu aies à tout refaire plus tard.



venv\Scripts\activate 

Phase 0 — Fondations du projet (avant tout code métier)
Choisir la structure du repo en microservices dès le départ (monorepo avec dossiers séparés, pas un gros fichier monolithique) :
  /services
    /hr-agent
    /it-agent
    /orchestrator (routing + fusion)
    /mcp-servers
      /hrisp-mcp
      /policy-mcp
      /jira-mcp
    /shared (schemas, types, utils communs)
  /infra (docker-compose, k8s manifests)
  /eval (golden datasets, scripts RAGAS)
Choisir le langage/stack : Python (FastAPI) est le standard pour agents LLM + MCP ; possible aussi en TypeScript/Node si tu préfères
Définir un schéma de message commun entre microservices (ex: Pydantic models partagés) — requête employé, réponse agent, decision object
Mettre en place Git + structure de branches, .env géré proprement (jamais de clé API en dur)
Choisir l'orchestrateur agentic : LangGraph (recommandé, gère bien les state machines multi-agents)
Choisir le vector store : Qdrant ou pgvector (les deux sont gratuits/self-hostable, bons pour un portfolio)
Choisir l'outil d'observabilité dès le départ : Langfuse (self-hostable, gratuit) — le brancher tôt, pas à la fin
Phase 1 — Partie RH (ton focus actuel)

1.1 Données et ingestion

Récupérer le PDF Clark County + un 2e document pour varier les sources
Écrire le pipeline d'ingestion : extraction texte → chunking (par section, pas juste par taille fixe) → embeddings → stockage vector DB
Ajouter les métadonnées à chaque chunk (section_id, titre, page) — indispensable pour l'évaluation et pour BM25

1.2 Retrieval

Implémenter le RAG simple d'abord (embeddings only) — baseline
Implémenter BM25 en parallèle (ex: avec rank_bm25 ou Elasticsearch/Opensearch)
Fusionner les deux (Reciprocal Rank Fusion)
Ajouter le reranker (Cohere Rerank API ou un cross-encoder open-source type bge-reranker)

1.3 Golden dataset + évaluation

Construire le golden dataset (50-100 questions) à partir du PDF
Mettre en place RAGAS, comparer RAG simple vs hybrid+rerank
Documenter les résultats (c'est ta preuve chiffrée pour le portfolio)

1.4 MCP Server HRIS

Créer une base de données factice (PostgreSQL ou SQLite) simulant les données employés : congés, contrat, notes de frais
Coder le serveur MCP HRIS avec le SDK officiel (Python ou TS) exposant des tools : get_leave_balance, get_contract_status, submit_leave_request
Tester le serveur MCP indépendamment (avec l'inspecteur MCP ou un client de test simple)

1.5 HR Agent (orchestration)

Construire le graph LangGraph : réception question → décision (RAG seul / HRIS seul / les deux) → réponse
Ajouter le HR Verifier Agent (contrôle qualité, décide auto-résolution vs approbation humaine)
Ajouter l'Escalation Agent (notif Slack/email pour cas sensibles)

1.6 API du microservice HR

Exposer le HR Agent via FastAPI (endpoint /hr/query)
Ajouter guardrails : PII redaction, détection de prompt injection basique
Logger chaque requête vers Langfuse pour observabilité

1.7 Tests et packaging

Tests unitaires (retrieval, tools MCP) et tests d'intégration (bout en bout)
Dockeriser le service HR (Dockerfile propre, image légère)
Phase 2 — Partie IT (une fois HR fonctionnel et stable)
Répéter la même mécanique que HR : corpus de runbooks IT (à trouver ou générer), vector store IT séparé
Serveur MCP Jira (créer ticket, vérifier permissions, reset accès) — utiliser l'API réelle de Jira en mode sandbox/dev si possible, sinon simuler
IT Agent avec sa propre logique de décision (souvent plus orienté actions/diagnostics que HR)
IT Verifier Agent + Escalation
Microservice IT indépendant, même structure que HR (réutilise le code partagé dans /shared)
Phase 3 — Fusion / Orchestrateur global
Construire l'Intent Router Agent : reçoit la requête brute, classe IT / HR / ambigu / les deux
Construire le routing logic : appelle le microservice HR et/ou IT selon la classification, gère les cas de clarification
Gérer le cas "question mixte" (ex: un problème touchant à la fois accès IT et policy RH) — c'est le vrai test d'architecture multi-agent
Centraliser les logs/traces de tous les microservices dans Langfuse pour une vue unifiée
Phase 4 — Robustesse et sécurité (transverse, à ne pas laisser à la fin)
Contrôle d'accès entre agents (HR agent ne doit jamais voir les données Jira sensibles et inversement)
Rate limiting sur les endpoints
Tests de prompt injection (essayer de faire dérailler l'agent avec des inputs malveillants)
Cache sémantique pour les questions répétitives (réduit coût + latence)
Phase 5 — Déploiement
Docker Compose pour faire tourner tous les microservices + vector DB + Langfuse localement
CI/CD basique (GitHub Actions : lint, tests, build image)
Déploiement cible : Railway/Render (simple, gratuit pour portfolio) ou k8s si tu veux viser plus "senior" (minikube en local suffit pour démontrer la compétence)
Documentation d'architecture (README avec diagrammes, décisions techniques justifiées — c'est ce qui compte le plus pour montrer ton niveau)
Ce que tu dois savoir/apprendre en parallèle (prérequis techniques)
Python avancé : async/await (indispensable pour appels API concurrents), Pydantic pour la validation de schémas
FastAPI : routes, dependency injection, gestion d'erreurs
LangGraph : concepts de state graph, nodes, edges conditionnelles, checkpointing
Protocole MCP : concepts resources/tools/prompts, comment coder un serveur avec le SDK officiel
Vector databases : comment fonctionne la similarity search, indexation HNSW
BM25 : concept de scoring TF-IDF, pourquoi il complète les embeddings
RAGAS : comment set up les métriques d'évaluation RAG
Docker : Dockerfile multi-stage, docker-compose pour orchestrer plusieurs services
Observabilité LLM : concepts de tracing (spans, tokens, latence, coût par requête)




////////////////////////////////////////////////////////////////////////////////////
Principe de découpage : un microservice = une responsabilité déployable indépendamment

La règle : un microservice doit pouvoir être déployé, scalé et redémarré seul, sans casser les autres. Voici comment je découperais ton système.

Les microservices (déployables séparément)

1. orchestrator-service

Rôle : reçoit la requête employé, fait l'Intent Routing, appelle HR et/ou IT, fusionne les réponses si besoin
Expose : POST /query (le seul point d'entrée public pour l'employé)
Appelle : hr-service et it-service en interne (HTTP ou message queue)
Pourquoi séparé : c'est le seul composant qui a besoin de savoir que HR et IT existent tous les deux — HR et IT n'ont pas besoin de se connaître entre eux

2. hr-service

Rôle : HR Agent + HR Verifier + Escalation Agent (tout le pipeline RH)
Expose : POST /hr/query (interne, appelé par l'orchestrator — pas exposé publiquement)
Appelle en interne : hr-rag-service (ou l'inclut directement) + mcp-hris-service
Pourquoi séparé : tu peux le scaler indépendamment (si HR reçoit 10x plus de trafic que IT), le redéployer sans toucher à IT, et le tester isolément

3. it-service

Même logique que HR, côté IT (IT Agent + Verifier + Escalation)
Expose : POST /it/query (interne)

4. mcp-hris-service

Rôle : le serveur MCP qui expose les tools HRIS (get_leave_balance, etc.) par-dessus la DB employés
Expose : le protocole MCP standard (SSE ou stdio selon ton setup)
Pourquoi séparé : un serveur MCP est censé être réutilisable — potentiellement par d'autres agents/clients dans le futur, pas juste ton HR Agent. Le séparer respecte l'esprit du protocole.

5. mcp-jira-service

Même logique côté IT (tools Jira : create_ticket, check_user_permissions...)

6. mcp-policy-service (optionnel, si tu veux exposer le RAG lui-même en MCP)

Expose search_hr_policies et search_it_runbooks comme tools MCP
Alternative plus simple : garder le RAG comme une simple fonction Python importée directement dans hr-service, sans microservice dédié — à toi de choisir le niveau de granularité. Pour un portfolio, séparer le RAG en microservice montre une compréhension plus poussée, mais ce n'est pas obligatoire au début.

Infra partagée (pas des microservices métier, mais des services d'infra)

vector-db (Qdrant, conteneur à part)
postgres (données HRIS + Jira simulées)
langfuse (observabilité, conteneur à part, souvent fourni en self-host docker-compose)
Schéma de communication
Employee
   ↓ HTTP
orchestrator-service (port 8000)
   ↓ HTTP interne        ↓ HTTP interne
hr-service (8001)      it-service (8002)
   ↓ MCP protocol          ↓ MCP protocol
mcp-hris-service (8010)  mcp-jira-service (8011)
   ↓ SQL                    ↓ REST/SQL
postgres (HRIS data)     postgres (Jira simulé) ou vraie API Jira

hr-service / it-service → vector-db (Qdrant) pour le RAG
hr-service / it-service → langfuse pour le tracing
Comment ils communiquent concrètement
Orchestrator → HR/IT service : HTTP REST simple (POST /hr/query avec un JSON {employee_id, question}) — pas besoin de message queue à cette échelle, ça complexifierait inutilement
HR/IT service → MCP servers : protocole MCP natif (pas du REST classique) — c'est géré par le client MCP que tu instancies dans ton agent LangGraph
Si tu veux montrer une compétence supplémentaire plus tard : tu peux introduire une queue (RabbitMQ/Redis) entre orchestrator et les services pour du traitement asynchrone (utile si une requête prend du temps) — mais ce n'est pas nécessaire au début, à garder pour une itération avancée
Pourquoi ce découpage précis (et pas plus fin, ni plus gros)
Pas un seul gros service monolithique → tu perdrais tout l'intérêt "microservices" pour ton portfolio, et tu ne pourrais pas scaler HR indépendamment d'IT
Pas un microservice par agent individuel (un service pour HR Agent, un autre pour HR Verifier, un autre pour Escalation) → trop fin, complexité réseau inutile pour la valeur ajoutée. Les agents internes à HR restent des nodes LangGraph dans le même service hr-service — ils communiquent en mémoire, pas via HTTP.
Ce que ça donne pour TA phase actuelle (juste HR)

Tu n'as besoin de démarrer que 3 services pour l'instant :

hr-service        (le cœur : agent + RAG + verifier)
mcp-hris-service  (tools sur données employés)
vector-db + postgres (infra)

L'orchestrator et IT viendront en Phase 2/3, mais la frontière hr-service que tu codes maintenant doit déjà exposer une API HTTP propre (POST /hr/query) pour être branchable par l'orchestrator plus tard sans rien casser.