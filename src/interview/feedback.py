feedback_provider = None


def get_feedback_provider():
    global feedback_provider
    return feedback_provider


def set_feedback_provider(fbp):
    global feedback_provider
    feedback_provider = fbp
