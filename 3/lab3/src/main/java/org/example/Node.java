package org.example;

import java.io.IOException;
import java.net.DatagramSocket;
import java.net.DatagramPacket;
import java.net.InetSocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.concurrent.ThreadLocalRandom;


public class Node {
    private static final ObjectMapper mapper = new ObjectMapper();

    private DatagramSocket socket;
    private InetSocketAddress ownAddress;
    private int ownStorage;
    private List<StorageEntry> topStorage = new ArrayList<>();

    private List<InetSocketAddress> neighborNodes;
    private InetSocketAddress controllerAddress;

    private boolean informed = false;
    private boolean initiator = false;
    private InetSocketAddress upwardNode = null;
    private int neighborInformed = 0;


    public Node(InetSocketAddress ownAddress, int storage, InetSocketAddress controllerAddress, List<InetSocketAddress> neighborNodes) throws SocketException {
        this.ownAddress = ownAddress;
        this.ownStorage = storage;
        this.controllerAddress = controllerAddress;
        this.neighborNodes = new ArrayList<>(neighborNodes);

        this.topStorage.add(new StorageEntry(ownAddress.getHostString() + ":" + ownAddress.getPort(), storage));
        this.socket = new DatagramSocket(ownAddress.getPort(), ownAddress.getAddress());
    }


    public void startListening() throws IOException {
        Thread listenThread = new Thread(() -> {
            byte[] incomingBuffer = new byte[1024 * 8];
            while(!socket.isClosed()){
               try{
                   DatagramPacket incomingPacket = new DatagramPacket(incomingBuffer, incomingBuffer.length);
                   socket.receive(incomingPacket);

                   InetSocketAddress fromNeighbor = new InetSocketAddress(incomingPacket.getAddress(), incomingPacket.getPort());
                   Message message = jsonDeserializer(incomingPacket.getData(), incomingPacket.getLength());
                     if (message != null) {
                          onReceive(message, fromNeighbor);
                          int latency = ThreadLocalRandom.current().nextInt(0, 100 - 1);
                          Thread.sleep(latency);
                     }
               } catch (Exception e) {
                   if (socket.isClosed()) {
                       System.out.println("Socket was closed. Listener terminated.");
                       break;
                   }
                   System.err.println("error on package receive: " + e.getMessage());
               }
            }
        });
        listenThread.setDaemon(true);
        listenThread.start();
    }


    public void sendMessage(InetSocketAddress target, Message message) throws IOException {
        byte[] buffer = jsonSerializer(message);
        DatagramPacket packet = new DatagramPacket(buffer, buffer.length, target.getAddress(), target.getPort());
        socket.send(packet);

        if(!"R".equals(message.type)){
            byte[] logBuffer = jsonSerializer(
                    new LMessage(
                            String.valueOf(System.currentTimeMillis()),
                            ownAddress.getHostString() + ":" + ownAddress.getPort(),
                            target.getHostString() + ":" + target.getPort(),
                            message.type,
                            this.topStorage
                    )
            );
            DatagramPacket logPacket = new DatagramPacket(logBuffer, logBuffer.length, controllerAddress.getAddress(), controllerAddress.getPort());
            socket.send(logPacket);
        }
    }

    public void sendInitiate() throws IOException {
        this.informed = true;
        this.initiator = true;
        for (InetSocketAddress neighbor : neighborNodes) {
            sendMessage(neighbor, new IMessage());
        }
    }

    public synchronized void onReceive(Message message, InetSocketAddress fromNeighbor) throws IOException {
        if("S".equals(message.type)){
            sendInitiate();
            return;
        }

        if (!informed){
            upwardNode = fromNeighbor;
            informed = true;
            for (InetSocketAddress neighbor : neighborNodes) {
                if (!neighbor.equals(fromNeighbor)) {
                    sendMessage(neighbor, new IMessage());
                }
            }
        }

        if("I".equals(message.type) || "E".equals(message.type)){
            neighborInformed++;
        }

        if("E".equals(message.type) && message instanceof EMessage){
            List<StorageEntry> incomingTop = ((EMessage) message).topStorage;
            if (incomingTop != null) {
                this.topStorage.addAll(incomingTop);
            }
            Collections.sort(this.topStorage);
            if (this.topStorage.size() > 5) {
                this.topStorage = new ArrayList<>(this.topStorage.subList(0, 5));
            }
        }

        if (neighborInformed == neighborNodes.size()){
            if(initiator){
                sendMessage(controllerAddress, new RMessage(topStorage));
            } else {
                if(upwardNode != null){
                    sendMessage(upwardNode, new EMessage(topStorage));
                }
            }
        }
    }


    private byte[] jsonSerializer(Message message) {
        try {
            return mapper.writeValueAsBytes(message);
        } catch (Exception e) {
            System.err.println("error on JSON-serialization: " + e.getMessage());
            return new byte[0];
        }
    }

    private Message jsonDeserializer(byte[] data, int length) {
        try {
            return mapper.readValue(data, 0, length, Message.class);
        } catch (Exception e) {
            System.err.println("JSON Parser error: " + e.getMessage());
            return null;
        }
    }
}