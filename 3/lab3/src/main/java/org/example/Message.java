package org.example;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

import java.util.ArrayList;
import java.util.List;

@JsonTypeInfo(
        use = JsonTypeInfo.Id.NAME,
        include = JsonTypeInfo.As.EXISTING_PROPERTY,
        property = "type",
        visible = true
)
@JsonSubTypes({
        @JsonSubTypes.Type(value = IMessage.class, name = "I"),
        @JsonSubTypes.Type(value = SMessage.class, name = "S"),
        @JsonSubTypes.Type(value = EMessage.class, name = "E"),
        @JsonSubTypes.Type(value = RMessage.class, name = "R"),
        @JsonSubTypes.Type(value = LMessage.class, name = "L")
})

public class Message {
    public String type;

    public Message(){}

    public Message(String type) {
        this.type = type;
    }
}

abstract class DataMessage extends Message {
    public List<StorageEntry> topStorage = new ArrayList<>();

    public DataMessage(){}

    public DataMessage(String type, List<StorageEntry> topStorage) {
        super(type);
        if (topStorage != null) {
            this.topStorage = new ArrayList<>(topStorage);
        }
    }
}


class IMessage extends Message {
    public IMessage() {
        super("I");
    }
}

class SMessage extends Message{
    public SMessage() {
        super("S");
    }
}

class EMessage extends DataMessage {
    public EMessage() {super("E", null);}
    public EMessage(List<StorageEntry> topStorage) {
        super("E", topStorage);
    }
}

class RMessage extends DataMessage {
    public RMessage() {super("R", null);}
    public RMessage(List<StorageEntry> topStorage) {
        super("R", topStorage);
    }
}

class LMessage extends DataMessage {
    public String timestamp = "";
    public String startIpPort = "";
    public String targetIpPort = "";
    public String logType = "";
    public int loggedStorageValue;

    public LMessage() {super("L", null);}
    public LMessage(String timestamp, String startIpPort, String targetIpPort, String logType,List<StorageEntry> sumStorage) {
        super("L", sumStorage);
        this.timestamp = timestamp;
        this.startIpPort = startIpPort;
        this.targetIpPort = targetIpPort;
        this.logType = logType;
    }
}