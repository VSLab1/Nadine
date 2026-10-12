# Praktikum Verteilte Systeme

Dieses Repository enthält die im Rahmen des Praktikums **Verteilte Systeme** (Prof. Dr. Erwin Mayer) entwickelten Laborversuche[cite: 1, 16, 37]. Als Programmiersprachen wurden Java und Python eingesetzt, basierend auf Netzwerkinfrastrukturen mit UDP, gRPC und simulierten verteilten Netzwerken[cite: 7, 20, 42].

---

## 📋 Inhaltsverzeichnis
1. [Labor 1: Peer-to-Peer Computing (Multi-Player-Spiel)](#labor-1-peer-to-peer-computing-multi-player-spiel)
2. [Labor 2: gRPC-Programmierung (Chat-Anwendung & Service-Chaining)](#labor-2-grpc-programmierung-chat-anwendung--service-chaining)
3. [Labor 3: Verteilte Algorithmen (Echo-Algorithmus & Simulation)](#labor-3-verteilte-algorithmen-echo-algorithmus--simulation)

---

## Labor 1: Peer-to-Peer Computing (Multi-Player-Spiel)

Im ersten Versuch wurde eine einfache, verteilte Peer-to-Peer-Anwendung in Form eines Multi-Player-Spiels (angelehnt an das Prinzip von "Tron" / 4-Gewinnt-Spurstruktur) realisiert[cite: 1, 4, 8].

* **Architektur:** Pure Peer-to-Peer-Architektur (Friend-Ansatz über Join-Kommando, kein zentrales Routing nötig)[cite: 9].
* **Kommunikation:** Nachrichtenbasiert über **UDP-Sockets** unter Verwendung von **JSON** für die Datenstrukturen[cite: 9].
* **Funktionen (Teil 1):** 
  * Quadratisches Spielfeld ($M \times M$) mit konfigurierbarer Größe und bis zu 4 Spielern[cite: 8].
  * Steuerung über Pfeiltasten mit permanenter Hinterlassung einer Spur (Kollisionserkennung mit Wänden und Spuren führt zum Ausscheiden)[cite: 8].
  * Echtzeitsynchronisation aller Spielzustände zwischen den Peers und Visualisierung via GUI[cite: 9].
* **Erweiterungen (Teil 2):** 
  * Dynamische Gruppenzusammensetzung mit `Join`- und `Leave`-Kommandos[cite: 13].
  * Verwaltung von aktiven Online-Peers und automatisches Versenden von Nachrichten nur an erreichbare Teilnehmer[cite: 13].

---

## Labor 2: gRPC-Programmierung (Chat-Anwendung & Service-Chaining)

Der zweite Versuch widmete sich einer Service-orientierten Architektur (SOA) unter Einsatz von **gRPC (Google RPC)** und Protocol Buffers (Proto3) als Middleware[cite: 20, 21].

* **Technologien:** Java, gRPC, Protocol Buffers (`.proto`-Spezifikationen), IntelliJ[cite: 20].
* **Teilaufgabe 1 (Klassischer Chat):**
  * Registrierung von $N$ Chat-Teilnehmern ($2 < N \le 10$) über Nicknames mit Fehlerbehandlung bei Duplikaten[cite: 22].
  * Senden und Empfangen von Nachrichten an alle aktiven Teilnehmer sowie Abfrage der aktuellen Teilnehmerliste[cite: 22].
  * Verwendung von gRPC-Streaming-Mechanismen und `oneof`-Syntaxelementen[cite: 22].
  * Analyse von übertragenen Nachrichten auf Byte-Ebene (Hex-Dekodierung von String- und Integer-Feldern) mithilfe von **Wireshark**[cite: 28].
* **Teilaufgabe 2 (Service-Chaining / History-Server):**
  * Realisierung eines eigenständigen **History-Servers** als zusätzlicher Service[cite: 29].
  * Der Hauptserver spiegelt alle Chat-Einträge via gRPC-Stream auf den History-Server (*Service-Chaining*)[cite: 29].
  * Neue Clients werden beim Beitritt direkt mit der bisherigen Chat-Historie versorgt[cite: 29].

---

## Labor 3: Verteilte Algorithmen (Echo-Algorithmus & Simulation)

Im dritten Versuch wurden verteilte Algorithmen und Prinzipien zur Durchführung einer verteilten Berechnung (Summenbildung von Speicherplätzen im Netzwerk) ohne zentralen Koordinator untersucht[cite: 37, 41].

* **Kernkonzepte:** 
  * Anwendung des **Flooding-** und **Echo-Algorithmus** auf Basis von UDP-Nachrichten[cite: 41, 44].
  * Event/Action-Bauart von verteilten Algorithmen[cite: 39].
* **Simulationsumgebung:**
  * Ein in einer JSON-Datei (`mynet.json`) spezifiziertes Netzwerk mit $N \ge 10$ Knoten und zwischen $2N$ und $3N$ Kanten[cite: 45].
  * Jeder Knoten wird als eigener Prozess gestartet, gesteuert über eine Deployment-Komponente via Kommandozeilenargumente[cite: 45].
  * Simulation von variablen Nachrichten-Latenzen mittels künstlicher Verzögerungen (`sleep`)[cite: 45].
* **Controller-Prozess & Logging:**
  * Ein zentraler Controller stößt den Algorithmus an (START-Nachricht) und sammelt kontinuierlich `LOG`-Nachrichten (Zeitstempel, Absender, Empfänger, Nachrichtentyp I/E)[cite: 46].
  * Am Ende ermittelt und visualisiert der Controller die Gesamtsumme des verfügbaren Speichers sowie die Anzahl der ausgetauschten Nachrichten[cite: 46].
* **Erweiterungen (Heimarbeit & Remote-Deployment):**
  * Automatisiertes Remote-Starten von Prozessen über **SSH** (`Runtime.exec` / `ProcessBuilder`) auf verteilten Rechnern[cite: 48, 49].
  * Erweiterung des Algorithmus zur Ermittlung der **Top-5-Speicherplatzverbraucher** im Netzwerk[cite: 50].

---

## Ausführung & Start

* **Labor 1:** Kompilieren und Starten der Peer-Anwendungen mit Übergabe individueller Ports (z. B. mittels Loopback `127.0.0.1`)[cite: 6].
* **Labor 2:** Nutzen Sie `./gradlew clean build` zum Generieren der Stubs/Skeletons aus den `.proto`-Dateien und starten Sie zuerst den gRPC-Server, gefolgt von den Clients[cite: 23, 27].
* **Labor 3:** Konfigurieren Sie das Netzwerk in der `mynet.json` und starten Sie das System über den Controller bzw. die Deployment-Skripte[cite: 45, 47].

---
*Erstellt im Rahmen des Praktikums Verteilte Systeme.*
