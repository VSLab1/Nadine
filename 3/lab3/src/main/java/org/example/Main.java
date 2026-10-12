package org.example;

import java.net.InetSocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.List;


public class Main {
    public static void main(String[] args) throws SocketException {
        if (args.length < 4){
            System.out.println("not enough parameters provided, currently: " + args.length);
            System.exit(1);
        }

        try{
            InetSocketAddress ownAddress = parseAddress(args[0]);
            InetSocketAddress controllerAddress = parseAddress(args[1]);
            int storage = Integer.parseInt(args[2]);

            List<InetSocketAddress> neighborNodes = new ArrayList<>();
            for (int i = 3; i < args.length; i++) {
                neighborNodes.add(parseAddress(args[i]));
            }

            Node node = new Node(ownAddress, storage, controllerAddress, neighborNodes);
            node.startListening();
            Thread.currentThread().join();

        } catch (Exception e){
            System.err.println("Error initializing node: " + e.getMessage());
             System.exit(1);
        }
    }

    private static InetSocketAddress parseAddress(String addressString){
        String[] parts = addressString.split(":");
        if (parts.length != 2) {
            throw new IllegalArgumentException("Invalid address format: " + addressString);
        }
        return new InetSocketAddress(parts[0], Integer.parseInt(parts[1]));
    }
}