package org.example;

import java.net.InetSocketAddress;

public class StorageEntry implements Comparable<StorageEntry> {
    public String address;
    public int storage;

    public StorageEntry(){};
    public StorageEntry(String address, int storage) {
        this.address = address;
        this.storage = storage;
    }

    @Override
    public int compareTo(StorageEntry o) {
        // Absteigend sortieren (höchster Speicher zuerst)
        return Integer.compare(o.storage, this.storage);
    }
}
