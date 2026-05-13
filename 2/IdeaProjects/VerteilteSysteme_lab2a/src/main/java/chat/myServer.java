package chat;

import com.google.protobuf.Empty;
import io.grpc.Grpc;
import io.grpc.InsecureServerCredentials;
import io.grpc.Server;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.Map;
import java.util.logging.Logger;
import java.util.concurrent.ConcurrentHashMap;

public class myServer {
    private static final Logger logger = Logger.getLogger(myServer.class.getName());
    private static final Map<String, StreamObserver<MemberOptions>> clients = new ConcurrentHashMap<>();
    private static final int MAX_MEMBERS = 3;

    public static void main(String[] args) throws IOException, InterruptedException{
        int port = 50051;
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
                                currentNickname = nickname;
                                clients.put(currentNickname, responseObserver);
                                responseObserver.onNext(createStatusResponse(GetJoinStatus.SUCCESS));

                                MemberOptions joinNotification = MemberOptions.newBuilder()
                                        .setJoin(JoinChat.newBuilder().setNickname(currentNickname).build())
                                        .build();

                                clients.forEach((name, observer) -> {
                                    if(!name.equals(currentNickname)){
                                        observer.onNext(joinNotification);
                                    }
                                });

                                System.out.println(currentNickname + "joined the chat");
                            }
                            break;
                        case SEND:
                            ChatMsg msg = value.getSend();
                            System.out.println("Broadcast: " + currentNickname + ": " + msg.getText());

                            MemberOptions broadcastMsg = MemberOptions.newBuilder()
                                    .setSend(ChatMsg.newBuilder()
                                            .setNickname(currentNickname)
                                            .setText(msg.getText())
                                            .build())
                                    .build();

                            clients.forEach((name, observer) -> {
                                if (!name.equals(currentNickname)) {
                                    observer.onNext(broadcastMsg);
                                }
                            });
                            break;
                        case LEAVE:
                            handleLeave();
                            break;
                        default:
                            break;

                    }
                }

                private void handleLeave() {
                    if (currentNickname != null) {
                        StreamObserver<MemberOptions> removed = clients.remove(currentNickname);
                        if(removed != null){
                            MemberOptions info = MemberOptions.newBuilder()
                                    .setLeave(LeaveChat.newBuilder().setNickname(currentNickname).build())
                                    .build();
                            clients.values().forEach(observer -> observer.onNext(info));
                            currentNickname = null;
                        }
                        String text = currentNickname + " has left the chat";
                        System.out.println(text);
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

