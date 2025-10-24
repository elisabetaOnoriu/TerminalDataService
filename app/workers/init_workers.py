import threading
from app.workers.kafka_producer_worker import KafkaProducerWorker
from app.workers.kafka_consumer_worker import KafkaConsumerWorker
from app.workers.sqs_consumer_worker import SqsConsumerWorker
from app.workers.sqs_producer_worker import SqsProducerWorker
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

def handle_message(msg: dict):
    print(f"[{threading.current_thread().name}] Event recieved: {msg}")

def init_kafka():
    admin = KafkaAdminClient(bootstrap_servers=["localhost:9092"])
    consumerKafka=KafkaConsumerWorker("topic", "localhost:9092", "my-group", handler=handle_message)

    producerKafka=KafkaProducerWorker("topic","localhost:9092")
    try:
        admin.create_topics([NewTopic(name="topic", num_partitions=1, replication_factor=1)])
    except TopicAlreadyExistsError:
        pass
    admin.close()
    for i in range(1,6):
            producerKafka.source.put({"emit event kafka": i})
    return producerKafka,consumerKafka, 

def init_sqs():
    sqsConsumer=SqsConsumerWorker(handler=handle_message)
    sqsProducer = SqsProducerWorker()

    for i in range(1,11):
        sqsProducer.enqueue({"emit event sqs ": i})
    return sqsProducer,sqsConsumer
