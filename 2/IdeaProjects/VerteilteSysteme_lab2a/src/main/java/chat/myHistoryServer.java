package chat;

import com.google.protobuf.Empty;
import io.grpc.Grpc;
import io.grpc.InsecureServerCredentials;
import io.grpc.Server;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

public class myHistoryServer {
    private static final Logger logger = Logger.getLogger(myHistoryServer.class.getName());
    private final List<MemberOptions> chatHistory = Collections.synchronizedList(new ArrayList<>());

    public static void main(String[] args) throws IOException, InterruptedException{
        int port = 50052;
        myHistoryServer historyServer = new myHistoryServer();

        Server server = Grpc.newServerBuilderForPort(port, InsecureServerCredentials.create())
                .addService(historyServer.new HistoryServiceImpl())
                .build()
                .start();

        logger.info("History-Server started on port " + port);
        server.awaitTermination();
    }

    private class HistoryServiceImpl extends HistoryServiceGrpc.HistoryServiceImplBase {

        @Override
        public void getHistory(Empty request, StreamObserver<History> responseObserver) {
            History response = History.newBuilder()
                    .addAllHistory(new ArrayList<>(chatHistory))
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
        }

        @Override
        public StreamObserver<MemberOptions> registerChat(StreamObserver<Empty> responseObserver){
            return new StreamObserver<MemberOptions>() {
                @Override
                public void onNext(MemberOptions memberOptions) {
                    chatHistory.add(memberOptions);
                    logger.info("History updated Typ: " + memberOptions.getOptionTypeCase());
                }

                @Override
                public void onError(Throwable throwable) {
                    logger.warning("Connection to Main server cancelled: " + throwable.getMessage());
                }

                @Override
                public void onCompleted() {
                    responseObserver.onNext(Empty.getDefaultInstance());
                    responseObserver.onCompleted();
                }
            };
        }
    }
}
