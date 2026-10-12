# Praktikum Verteilte Systeme

Dieses Repository enthält die im Rahmen des Praktikums **Verteilte Systeme** (Prof. Dr. Erwin Mayer) entwickelten Laborversuche. Als Programmiersprachen wurden Java und Python eingesetzt, basierend auf Netzwerkinfrastrukturen mit UDP, gRPC und simulierten verteilten Netzwerken.

---

## 📋 Inhaltsverzeichnis
1. [Labor 1: Peer-to-Peer Computing (Multi-Player-Spiel)](#labor-1-peer-to-peer-computing-multi-player-spiel)
2. [Labor 2: gRPC-Programmierung (Chat-Anwendung & Service-Chaining)](#labor-2-grpc-programmierung-chat-anwendung--service-chaining)
3. [Labor 3: Verteilte Algorithmen (Echo-Algorithmus & Simulation)](#labor-3-verteilte-algorithmen-echo-algorithmus--simulation)

---

## Labor 1: Peer-to-Peer Computing (Multi-Player-Spiel)

Im ersten Versuch wurde eine einfache, verteilte Peer-to-Peer-Anwendung in Form eines Multi-Player-Spiels (angelehnt an das Prinzip von "Tron" / 4-Gewinnt-Spurstruktur) realisiert.

* **Architektur:** Pure Peer-to-Peer-Architektur (Friend-Ansatz über Join-Kommando, kein zentrales Routing nötig).
* **Kommunikation:** Nachrichtenbasiert über **UDP-Sockets** unter Verwendung von **JSON** für die Datenstrukturen.
* **Funktionen (Teil 1):** 
  * Quadratisches Spielfeld ($M \times M$) mit konfigurierbarer Größe und bis zu 4 Spielern.
  * Steuerung über Pfeiltasten mit permanenter Hinterlassung einer Spur (Kollisionserkennung mit Wänden und Spuren führt zum Ausscheiden).
  * Echtzeitsynchronisation aller Spielzustände zwischen den Peers und Visualisierung via GUI.
* **Erweiterungen (Teil 2):** 
  * Dynamische Gruppenzusammensetzung mit `Join`- und `Leave`-Kommandos.
  * Verwaltung von aktiven Online-Peers und automatisches Versenden von Nachrichten nur an erreichbare Teilnehmer.

---

## Labor 2: gRPC-Programmierung (Chat-Anwendung & Service-Chaining)

Der zweite Versuch widmete sich einer Service-orientierten Architektur (SOA) unter Einsatz von **gRPC (Google RPC)** und Protocol Buffers (Proto3) als Middleware.

* **Technologien:** Java, gRPC, Protocol Buffers (`.proto`-Spezifikationen), IntelliJ.
* **Teilaufgabe 1 (Klassischer Chat):**
  * Registrierung von $N$ Chat-Teilnehmern ($2 < N \le 10$) über Nicknames mit Fehlerbehandlung bei Duplikaten.
  * Senden und Empfangen von Nachrichten an alle aktiven Teilnehmer sowie Abfrage der aktuellen Teilnehmerliste.
  * Verwendung von gRPC-Streaming-Mechanismen und `oneof`-Syntaxelementen.
  * Analyse von übertragenen Nachrichten auf Byte-Ebene (Hex-Dekodierung von String- und Integer-Feldern) mithilfe von **Wireshark**.
* **Teilaufgabe 2 (Service-Chaining / History-Server):**
  * Realisierung eines eigenständigen **History-Servers** als zusätzlicher Service.
  * Der Hauptserver spiegelt alle Chat-Einträge via gRPC-Stream auf den History-Server (*Service-Chaining*).
  * Neue Clients werden beim Beitritt direkt mit der bisherigen Chat-Historie versorgt.

---

## Labor 3: Verteilte Algorithmen (Echo-Algorithmus & Simulation)

Im dritten Versuch wurden verteilte Algorithmen und Prinzipien zur Durchführung einer verteilten Berechnung (Summenbildung von Speicherplätzen im Netzwerk) ohne zentralen Koordinator untersucht.

* **Kernkonzepte:** 
  * Anwendung des **Flooding-** und **Echo-Algorithmus** auf Basis von UDP-Nachrichten.
  * Event/Action-Bauart von verteilten Algorithmen.
* **Simulationsumgebung:**
  * Ein in einer JSON-Datei (`mynet.json`) spezifiziertes Netzwerk mit $N \ge 10$ Knoten und zwischen $2N$ und $3N$ Kanten.
  * Jeder Knoten wird als eigener Prozess gestartet, gesteuert über eine Deployment-Komponente via Kommandozeilenargumente.
  * Simulation von variablen Nachrichten-Latenzen mittels künstlicher Verzögerungen (`sleep`).
* **Controller-Prozess & Logging:**
  * Ein zentraler Controller stößt den Algorithmus an (START-Nachricht) und sammelt kontinuierlich `LOG`-Nachrichten (Zeitstempel, Absender, Empfänger, Nachrichtentyp I/E).
  * Am Ende ermittelt und visualisiert der Controller die Gesamtsumme des verfügbaren Speichers sowie die Anzahl der ausgetauschten Nachrichten.
* **Erweiterungen (Heimarbeit & Remote-Deployment):**
  * Automatisiertes Remote-Starten von Prozessen über **SSH** (`Runtime.exec` / `ProcessBuilder`) auf verteilten Rechnern.
  * Erweiterung des Algorithmus zur Ermittlung der **Top-5-Speicherplatzverbraucher** im Netzwerk.

---
*Erstellt im Rahmen des Praktikums Verteilte Systeme.*
