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
                            StreamObserver<MemberOptions> my_observer = responseObserver;
                            if (clients.containsKey(nickname)) {
                                my_observer.onNext(createStatusResponse(GetJoinStatus.NAME_TAKEN));
                            } else if (clients.size() >= MAX_MEMBERS) {
                                my_observer.onNext(createStatusResponse(GetJoinStatus.CHAT_FULL));
                            } else {
                                currentNickname = nickname;
                                clients.put(nickname, my_observer);
                                my_observer.onNext(createStatusResponse(GetJoinStatus.SUCCESS));

                                MemberOptions info = MemberOptions.newBuilder()
                                        .setJoin(JoinChat.newBuilder().setNickname(currentNickname).build())
                                        .build();
                                clients.values().forEach(observer -> observer.onNext(info));

                                System.out.println(currentNickname + "joined the chat");
                            }
                            break;
                        case SEND:
                            ChatMsg msg = value.getSend();
                            String formattedText = msg.getNickname() + ": " + msg.getText();
                            System.out.println("Broadcast: " + formattedText);

                            MemberOptions broadcastMsg = MemberOptions.newBuilder()
                                    .setSend(ChatMsg.newBuilder()
                                            .setNickname(msg.getNickname())
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
                        clients.remove(currentNickname);
                        String text = currentNickname + " has left the chat";
                        MemberOptions info = MemberOptions.newBuilder()
                                .setLeave(LeaveChat.newBuilder().setNickname(currentNickname).build())
                                .build();
                        clients.values().forEach(observer -> observer.onNext(info));
                        System.out.println(text);
                        currentNickname = null;
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

