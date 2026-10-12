package org.example;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetSocketAddress;
import java.net.SocketException;
import java.util.HashSet;
import java.util.List;
import java.util.Scanner;
import java.util.Set;

public class Controller {
    private static final ObjectMapper mapper = new ObjectMapper();
    private static int iCount = 0;
    private static int eCount = 0;

    public static void main(String[] args) {
        int controllerPort = 9999;
        String jsonPath = "mynet.json";

        try (DatagramSocket socket = new DatagramSocket(controllerPort)) {
            System.out.println("Controller is running on port " + controllerPort);
            printNetworkSummary(jsonPath);

            Thread receiverThread = new Thread(() -> {
                while (!socket.isClosed()) {
                    try {
                        byte[] buffer = new byte[1024 * 4];
                        DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                        socket.receive(packet);

                        String jsonString = new String(packet.getData(), 0, packet.getLength(), java.nio.charset.StandardCharsets.UTF_8).trim();
                        if(jsonString.isEmpty()) {
                            continue;
                        }
                        Message message = mapper.readValue(jsonString, Message.class);

                        if (message instanceof LMessage logMessage) {
                            System.out.println("Received Log:" + mapper.writeValueAsString(logMessage));

                            if("E".equals(logMessage.logType)){
                                eCount++;
                            } else if("I".equals(logMessage.logType)){
                                iCount++;
                            }
                        } else if ("R".equals(message.type)) {
                            System.out.println("\n========================================");
                            System.out.println("INFO: 'R'-Message received. Counter summary:");
                            System.out.println("Total 'I' Messages received: " + iCount);
                            System.out.println("Total 'E' Messages received: " + eCount);
                            System.out.println("========================================\n");
                            System.out.println("Received Result:" + mapper.writeValueAsString(message));
                        }

                    } catch (Exception e) {
                        System.err.println("error when receiving in Controller: " + e.getMessage());
                    }
                }
            });
            receiverThread.setDaemon(true);
            receiverThread.start();

            Thread.sleep(1000);

            Scanner scanner = new Scanner(System.in);
            System.out.println("Insert the Initiator node port or 'exit': ");

            while (true) {
                String input = scanner.nextLine();
                if (input.equalsIgnoreCase("exit")) {
                    System.out.println("Exiting Controller.");
                    break;
                }
                try {
                    int initiatorPort = Integer.parseInt(input);
                    InetSocketAddress initiatorAddress = new InetSocketAddress("localhost", initiatorPort);

                    SMessage startMessage = new SMessage();
                    byte[] data = mapper.writeValueAsBytes(startMessage);

                    DatagramPacket packet = new DatagramPacket(data, data.length, initiatorAddress.getAddress(), initiatorAddress.getPort());
                    socket.send(packet);
                } catch (NumberFormatException e) {
                    System.err.println("Invalid port number. Please enter a valid integer or 'exit'.");
                } catch (Exception e) {
                    System.err.println("Error when sending S message: " + e.getMessage());
                }
            }
        } catch (InterruptedException | SocketException e) {
            throw new RuntimeException(e);
        }
    }

    private static void printNetworkSummary(String jsonPath) {
        try {
            File jsonFile = new File(jsonPath);
            if (!jsonFile.exists()) {
                System.out.println(jsonPath + " not found skipped overview");
                return;
            }

            List<Deployment.NodeConfig> configs = mapper.readValue(jsonFile, new TypeReference<List<Deployment.NodeConfig>>() {});

            int totalNodes = configs.size();
            Set<String> uniqueEdges = new HashSet<>();

            for (Deployment.NodeConfig node : configs) {
                String nodeAddr = node.address;
                if (node.neighbors == null) continue;
                for (String neighborAddr : node.neighbors) {
                    String edgeKey = nodeAddr.compareTo(neighborAddr) < 0
                            ? nodeAddr + " <-> " + neighborAddr
                            : neighborAddr + " <-> " + nodeAddr;
                    uniqueEdges.add(edgeKey);
                }
            }

            System.out.println("--- NETWORK ---");
            System.out.println("Nodes: " + totalNodes);
            System.out.println("Edges : " + uniqueEdges.size());
            System.out.println("------------------------------------------------");

        } catch (Exception e) {
            System.err.println("error when creating network overview: " + e.getMessage());
        }
    }
}
