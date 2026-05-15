package chat;

import com.google.protobuf.Empty;
import io.grpc.Grpc;
import io.grpc.InsecureServerCredentials;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.Server;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.Map;
import java.util.logging.Logger;
import java.util.concurrent.ConcurrentHashMap;

public class myServer {
    private static final Logger logger = Logger.getLogger(myServer.class.getName());
    private static final Map<String, StreamObserver<MemberOptions>> clients = new ConcurrentHashMap<>();
    private static final int MAX_MEMBERS = 10;

    private static HistoryServiceGrpc.HistoryServiceBlockingStub historyBlockingStub;
    private static HistoryServiceGrpc.HistoryServiceStub historyAsyncStub;
    private static StreamObserver<MemberOptions> historyMirrorStream;

    public static void main(String[] args) throws IOException, InterruptedException{
        int port = 50051;

        ManagedChannel historyChannel = Grpc.newChannelBuilder("localhost:50052", InsecureChannelCredentials.create())
                .build();

        historyBlockingStub = HistoryServiceGrpc.newBlockingStub(historyChannel);
        historyAsyncStub = HistoryServiceGrpc.newStub(historyChannel);
        historyMirrorStream = historyAsyncStub.registerChat(new StreamObserver<Empty>() {
            @Override
            public void onNext(Empty empty) {}

            @Override
            public void onError(Throwable throwable) {}

            @Override
            public void onCompleted() {}
        });

        Server server = Grpc.newServerBuilderForPort(port, InsecureServerCredentials.create())
                .addService(new ChatServiceImpl())
                .build()
                .start();

        logger.info("Server started, listening on " + port);
        server.awaitTermination();
    }

    static class ChatServiceImpl extends ChatServiceGrpc.ChatServiceImplBase {


        @Override
        public void getMemberList(Empty request, StreamObserver<MemberList> responseObserver) {
            MemberList.Builder builder = MemberList.newBuilder();
            clients.keySet().forEach(name ->
                builder.addMembers(NewMember.newBuilder().setNickname(name).build())
            );
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        }

        @Override
        public StreamObserver<MemberOptions> registerStream(StreamObserver<MemberOptions> responseObserver) {

            return new StreamObserver<MemberOptions>() {
                private String currentNickname = null;

                @Override
                public void onNext(MemberOptions value) {
                    switch (value.getOptionTypeCase()) {
                        case JOIN:
                            String nickname = value.getJoin().getNickname();
                            if (clients.containsKey(nickname)) {
                                responseObserver.onNext(createStatusResponse(GetJoinStatus.NAME_TAKEN));
                            } else if (clients.size() >= MAX_MEMBERS) {
                                responseObserver.onNext(createStatusResponse(GetJoinStatus.CHAT_FULL));
                            } else {
                                History history = historyBlockingStub.getHistory(Empty.getDefaultInstance());
                                for (MemberOptions pastOption : history.getHistoryList()) {
                                    responseObserver.onNext(pastOption);
                                }

                                currentNickname = nickname;
                                clients.put(currentNickname, responseObserver);
                                responseObserver.onNext(createStatusResponse(GetJoinStatus.SUCCESS));

                                broadcast(value);

                                System.out.println(currentNickname + " joined the chat");
                            }
                            break;
                        case SEND:
                            System.out.println("Broadcast: " + currentNickname + ": " + value.getSend().getText());

                            MemberOptions broadcastMsg = MemberOptions.newBuilder()
                                    .setSend(value.getSend()
                                            .toBuilder()
                                            .setNickname(currentNickname)
                                            .build())
                                    .build();

                            broadcast(broadcastMsg);
                            break;
                        case LEAVE:
                            handleLeave();
                            break;
                        default:
                            break;

                    }
                }

                private void broadcast(MemberOptions option){
                    historyMirrorStream.onNext(option);
                    clients.forEach((name, observer) -> {
                        if (!name.equals(currentNickname)) {
                            observer.onNext(option);
                        }
                    });
                }

                private void handleLeave() {
                    if (currentNickname != null) {
                        if(clients.remove(currentNickname) != null){
                            MemberOptions leaveMsg = MemberOptions.newBuilder()
                                    .setLeave(LeaveChat.newBuilder().setNickname(currentNickname).build())
                                    .build();

                            broadcast(leaveMsg);
                            System.out.println(currentNickname + " has left the chat");
                            currentNickname = null;
                        }
                    }
                }

                private MemberOptions createStatusResponse(GetJoinStatus status) {
                    return MemberOptions.newBuilder()
                            .setGetStatus(GetStatus.newBuilder().setStatus(status).build())
                            .build();
                }

                @Override
                public void onError(Throwable t) {
                    handleLeave();
                }

                @Override
                public void onCompleted() {
                    handleLeave();
                    responseObserver.onCompleted();
                }
            };
        }
    }
}

