import data_center


def main():
    client = data_center.Client()
    print(client.get_all())
    print(client.get('FUCK'))


if __name__ == '__main__':
    main()
